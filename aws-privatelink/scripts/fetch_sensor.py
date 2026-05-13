#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "crowdstrike-falconpy>=1.4",
#   "truststore>=0.9",
# ]
# ///
"""Fetch the latest Falcon sensor RPM (AL2023) + tenant CID from the Falcon API.

Run via `uv run fetch_sensor.py ...`. uv will resolve and cache the
`crowdstrike-falconpy` dependency declared inline (PEP 723) on first run, so
no venv / pip setup is needed on the caller's machine.

Invoked by Terraform's `null_resource.sensor_fetch` in the
privatelink-stack module, but also runnable standalone for debugging.

Inputs (env or flags):
  FALCON_CLIENT_ID / --client-id      CrowdStrike API client ID
  FALCON_CLIENT_SECRET / --secret     CrowdStrike API client secret
  FALCON_BASE_URL / --base-url        Optional override (default: auto-discover)
  --cloud                             us-1 | us-2 | eu-1 (default: us-2)
  --arch                              x86_64 | aarch64 (default: x86_64)
  --out                               Output directory (required)

Output:
  <out>/falcon-sensor.rpm             The installer binary
  <out>/result.json                   { "cid": "...", "cloud": "us-2",
                                        "rpm_path": "...", "sha256": "..." }

Idempotent: skips re-download when the RPM on disk already matches the
expected sha256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

# Use the OS trust store (macOS Keychain, Windows cert store, Linux
# /etc/ssl) instead of certifi's bundled CAs. This is critical for
# customers behind corporate TLS inspection (Zscaler, Netskope, Palo Alto):
# their MITM root CA is installed in the OS trust store via MDM but is
# not in certifi, which causes SSL verification failures on Falcon API
# calls. truststore delegates to the platform, so whatever the OS trusts,
# Python trusts.
import truststore
truststore.inject_into_ssl()

from falconpy import SensorDownload


CLOUD_BASE_URLS = {
    "us-1": "https://api.crowdstrike.com",
    "us-2": "https://api.us-2.crowdstrike.com",
    "eu-1": "https://api.eu-1.crowdstrike.com",
}


def log(msg: str) -> None:
    print(f"[fetch_sensor] {msg}", file=sys.stderr, flush=True)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


ARCH_ALIASES = {
    "x86_64": ("x86_64", "amd64"),
    "aarch64": ("aarch64", "arm64"),
}


def pick_latest_al2023(installers: list[dict], arch: str) -> dict:
    arch_tokens = ARCH_ALIASES[arch]

    def is_al2023(i: dict) -> bool:
        if (i.get("platform") or "").lower() != "linux":
            return False
        name = (i.get("name") or "").lower()
        if not name.endswith(".rpm"):
            return False
        # Falcon splits these across os + os_version; some older records
        # cram both into os. Check the combined string either way.
        combined = f"{i.get('os') or ''} {i.get('os_version') or ''}".lower()
        if not ("amazon linux" in combined and "2023" in combined):
            return False
        # Architecture lives in the filename (.x86_64.rpm / .aarch64.rpm).
        # Falcon also has an `architectures` array on newer records.
        arch_field = [a.lower() for a in (i.get("architectures") or [])]
        return any(tok in name or tok in arch_field for tok in arch_tokens)

    candidates = [i for i in installers if is_al2023(i)]
    if not candidates:
        sample = [
            {
                "name": i.get("name"),
                "platform": i.get("platform"),
                "os": i.get("os"),
                "os_version": i.get("os_version"),
                "architectures": i.get("architectures"),
            }
            for i in installers[:8]
        ]
        raise SystemExit(
            f"No Amazon Linux 2023 {arch} sensor installer found. "
            f"First {len(sample)} of {len(installers)} installers returned: "
            f"{json.dumps(sample, indent=2)}"
        )
    candidates.sort(key=lambda i: i.get("release_date", ""), reverse=True)
    return candidates[0]


def handle_api_errors(resp: dict, context: str) -> dict:
    body = resp.get("body", {})
    if resp.get("status_code", 0) >= 400 or body.get("errors"):
        errors = body.get("errors") or [{"message": "unknown error"}]
        joined = "; ".join(e.get("message", str(e)) for e in errors)
        raise SystemExit(f"Falcon API error ({context}): {joined}")
    return body


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--cloud", default="us-2", choices=sorted(CLOUD_BASE_URLS))
    ap.add_argument(
        "--arch",
        default="x86_64",
        choices=sorted(ARCH_ALIASES),
        help="Target CPU architecture. x86_64 for t3/m5/c5 etc., aarch64 for Graviton (t4g/m6g/c6g).",
    )
    ap.add_argument("--client-id", default=os.environ.get("FALCON_CLIENT_ID"))
    ap.add_argument("--secret", default=os.environ.get("FALCON_CLIENT_SECRET"))
    ap.add_argument("--base-url", default=os.environ.get("FALCON_BASE_URL") or None)
    args = ap.parse_args()

    if not args.client_id or not args.secret:
        raise SystemExit(
            "Falcon API credentials required — set FALCON_CLIENT_ID + FALCON_CLIENT_SECRET "
            "or pass --client-id / --secret."
        )

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rpm_path = out_dir / "falcon-sensor.rpm"
    result_path = out_dir / "result.json"

    base_url = args.base_url or CLOUD_BASE_URLS[args.cloud]
    log(f"authenticating against {base_url}")

    sensor = SensorDownload(
        client_id=args.client_id,
        client_secret=args.secret,
        base_url=base_url,
    )

    log("fetching tenant CID")
    cid_body = handle_api_errors(sensor.get_sensor_installer_ccid(), "get_ccid")
    cid_list = cid_body.get("resources") or []
    if not cid_list:
        raise SystemExit("Falcon API returned no CID — check that the API key has Sensor Download: Read scope.")
    cid = cid_list[0]
    log(f"tenant CID: {cid[:8]}...{cid[-4:]}")

    log("listing AL2023 sensor installers")
    list_body = handle_api_errors(
        sensor.get_combined_sensor_installers_by_query(
            filter="platform:'linux'",
            sort="release_date|desc",
            limit=500,
        ),
        "list_installers",
    )
    installers = list_body.get("resources") or []
    if not installers:
        raise SystemExit("No Linux installers returned by Falcon API.")

    chosen = pick_latest_al2023(installers, args.arch)
    expected_sha = chosen["sha256"]
    version = chosen.get("version", "unknown")
    log(f"latest AL2023 sensor: {chosen['name']} (v{version}, sha256={expected_sha[:12]}...)")

    if rpm_path.exists() and sha256_of(rpm_path) == expected_sha:
        log("local RPM already matches expected sha256 — skipping download")
    else:
        log(f"downloading → {rpm_path}")
        resp = sensor.download_sensor_installer(id=expected_sha)
        if isinstance(resp, dict):
            body = handle_api_errors(resp, "download")
            raise SystemExit(f"Expected binary, got JSON: {body}")
        # falconpy returns raw bytes for binary downloads
        rpm_path.write_bytes(resp)
        actual_sha = sha256_of(rpm_path)
        if actual_sha != expected_sha:
            raise SystemExit(f"sha256 mismatch after download: expected {expected_sha}, got {actual_sha}")
        log("download verified")

    result = {
        "cid": cid,
        "cloud": args.cloud,
        "rpm_path": str(rpm_path),
        "sha256": expected_sha,
        "version": version,
    }
    result_path.write_text(json.dumps(result, indent=2))
    log(f"wrote {result_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
