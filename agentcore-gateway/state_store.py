"""
DynamoDB-backed request context store for correlating HTTP REQUEST and RESPONSE
interceptor invocations.

The AgentCore HTTP RESPONSE interceptor receives gatewayRequest=null, so any
metadata extracted during the REQUEST phase (provider, pointers, user_id, etc.)
must be persisted between the two Lambda invocations.  Both sides share the
REQUEST_ID from the Lambda client context as the key.

If DynamoDB is unavailable, save() and delete() log a warning and return
silently.  load() returns None, and the response handler falls back to
environment-variable defaults.  This degrades gracefully: response-side
redaction is skipped, but the gateway is not blocked.
"""

from __future__ import annotations

import json
import logging
import os
import time

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)

_TABLE = None


def _get_table():
    global _TABLE
    if _TABLE is None:
        _TABLE = boto3.resource("dynamodb").Table(os.environ["AIDR_STATE_TABLE"])
    return _TABLE


def save(request_id: str, ctx: dict, ttl_s: int = 300) -> None:
    """Persist request context keyed on request_id with a TTL."""
    try:
        _get_table().put_item(Item={
            "request_id": request_id,
            "ctx": json.dumps(ctx),
            "ttl": int(time.time()) + ttl_s,
        })
    except Exception as exc:
        logger.warning("state_store.save failed for %s: %s", request_id, exc)


def load(request_id: str) -> dict | None:
    """Return the persisted context for request_id, or None if absent."""
    try:
        resp = _get_table().get_item(Key={"request_id": request_id})
        item = resp.get("Item")
        return json.loads(item["ctx"]) if item else None
    except Exception as exc:
        logger.warning("state_store.load failed for %s: %s", request_id, exc)
        return None


def delete(request_id: str) -> None:
    """Remove the context entry after it has been consumed."""
    try:
        _get_table().delete_item(Key={"request_id": request_id})
    except Exception as exc:
        logger.warning("state_store.delete failed for %s: %s", request_id, exc)
