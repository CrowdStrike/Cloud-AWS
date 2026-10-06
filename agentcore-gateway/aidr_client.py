"""
CrowdStrike AIDR API client.

Bearer token is fetched from AWS Secrets Manager at cold-start and cached for
the lifetime of the Lambda execution environment.  Set AIDR_API_TOKEN directly
(without AIDR_API_TOKEN_SECRET_ARN) for local testing.

Uses only stdlib urllib.request for the outbound HTTP call — no httpx/requests
dependency required.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

import boto3

logger = logging.getLogger(__name__)

# Cached at cold-start; never re-fetched within the same execution environment.
_TOKEN: str | None = None


def _get_token() -> str:
    global _TOKEN
    if _TOKEN:
        return _TOKEN
    token = os.environ.get("AIDR_API_TOKEN")
    if token:
        _TOKEN = token
        return _TOKEN
    secret_arn = os.environ["AIDR_API_TOKEN_SECRET_ARN"]
    secret = boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)
    _TOKEN = secret["SecretString"]
    return _TOKEN


class AIDRUnreachableError(Exception):
    """Raised when the AIDR API is unreachable or returns a non-2xx status."""


def call_aidr(
    event_type: str,
    guard_input: dict,
    *,
    source_ip: str | None = None,
    app_id: str | None = None,
    user_id: str | None = None,
    llm_provider: str | None = None,
    model: str | None = None,
    model_version: str | None = None,
    source_location: str | None = None,
    tenant_id: str | None = None,
    collector_instance_id: str | None = None,
    timeout_s: float | None = None,
) -> dict:
    """
    POST to AIDR /aidr/aiguard/v1/guard_chat_completions.
    Returns the parsed JSON response dict.
    Raises AIDRUnreachableError on any connection or HTTP error.
    """
    endpoint = os.environ["AIDR_API_ENDPOINT"]
    if timeout_s is None:
        timeout_s = float(os.environ.get("AIDR_TIMEOUT_S", "3.0"))

    body: dict = {"event_type": event_type, "guard_input": guard_input}
    if source_ip:
        body["source_ip"] = source_ip
    if app_id:
        body["app_id"] = app_id
    if user_id:
        body["user_id"] = user_id
    if llm_provider:
        body["llm_provider"] = llm_provider
    if model:
        body["model"] = model
    if model_version:
        body["model_version"] = model_version
    if source_location:
        body["source_location"] = source_location
    if tenant_id:
        body["tenant_id"] = tenant_id
    if collector_instance_id:
        body["collector_instance_id"] = collector_instance_id

    url = f"{endpoint.rstrip('/')}/aidr/aiguard/v1/guard_chat_completions"
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {_get_token()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise AIDRUnreachableError(f"HTTP {exc.code}: {exc.read()}") from exc
    except Exception as exc:
        raise AIDRUnreachableError(str(exc)) from exc
