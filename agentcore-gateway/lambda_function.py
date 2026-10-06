"""
AWS Lambda entry point for the CrowdStrike AIDR AgentCore Gateway interceptor.

Dispatches to http_handler or mcp_handler based on the interceptor payload
shape, then on REQUEST vs RESPONSE based on whether gatewayResponse is present.

Payload shapes (interceptorInputVersion 1.0):
  HTTP REQUEST  — {"http": {"gatewayRequest":  {...}}}
  HTTP RESPONSE — {"http": {"gatewayResponse": {...}}}
  MCP REQUEST   — {"mcp": {"gatewayRequest":  {...}}}
  MCP RESPONSE  — {"mcp": {"gatewayRequest":  {...}, "gatewayResponse": {...}}}
"""

import base64
import json
import logging

import http_handler
import mcp_handler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_INTERNAL_ERROR_BODY = base64.b64encode(
    b'{"error":"Internal error during content inspection"}'
).decode()

_FALLBACK = {
    "interceptorOutputVersion": "1.0",
    "http": {
        "transformedGatewayResponse": {
            "statusCode": 500,
            "contentType": "application/json",
            "body": _INTERNAL_ERROR_BODY,
        }
    },
}


def lambda_handler(event: dict, context) -> dict:
    try:
        if "http" in event:
            if event["http"].get("gatewayResponse") is not None:
                return http_handler.handle_response(event, context)
            return http_handler.handle_request(event, context)

        if "mcp" in event:
            if event["mcp"].get("gatewayResponse") is not None:
                return mcp_handler.handle_response(event, context)
            return mcp_handler.handle_request(event, context)

        logger.warning("Unknown interceptor payload shape: %s", list(event.keys()))
        return {"interceptorOutputVersion": "1.0"}

    except Exception:
        logger.exception("Unhandled exception in lambda_handler — failing closed")
        return _FALLBACK
