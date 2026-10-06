import base64
import json


def decode_body(encoded: str) -> tuple[dict | None, bool]:
    """
    Decode a base64-encoded HTTP body from an AgentCore HTTP interceptor payload.
    Returns (parsed_dict, True) for valid JSON objects.
    Returns (None, False) for non-JSON, non-object, or decode errors.
    """
    try:
        raw = base64.b64decode(encoded)
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed, True
        return None, False
    except Exception:
        return None, False


def encode_body(obj: dict) -> str:
    """JSON-serialize and base64-encode a body dict for an AgentCore response."""
    return base64.b64encode(json.dumps(obj, separators=(",", ":")).encode()).decode()
