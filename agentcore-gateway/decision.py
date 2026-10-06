"""
Build AgentCore interceptor output dicts for each decision outcome.

All functions return a complete interceptorOutputVersion 1.0 dict that can be
returned directly from lambda_handler.
"""

from __future__ import annotations

import base64
import json


# ---------------------------------------------------------------------------
# HTTP target helpers
# ---------------------------------------------------------------------------

def http_passthrough() -> dict:
    return {"interceptorOutputVersion": "1.0", "http": {}}


def http_block(status: int, message: str) -> dict:
    body = json.dumps({"error": message, "code": "AIDR_BLOCKED"}, separators=(",", ":")).encode()
    return {
        "interceptorOutputVersion": "1.0",
        "http": {
            "transformedGatewayResponse": {
                "statusCode": status,
                "contentType": "application/json",
                "body": base64.b64encode(body).decode(),
            }
        },
    }


def http_error(message: str = "Internal error during content inspection") -> dict:
    return http_block(500, message)


def http_transformed_request(new_body: dict) -> dict:
    encoded = base64.b64encode(
        json.dumps(new_body, separators=(",", ":")).encode()
    ).decode()
    return {
        "interceptorOutputVersion": "1.0",
        "http": {"transformedGatewayRequest": {"body": encoded}},
    }


def http_transformed_response(new_body: dict) -> dict:
    encoded = base64.b64encode(
        json.dumps(new_body, separators=(",", ":")).encode()
    ).decode()
    return {
        "interceptorOutputVersion": "1.0",
        "http": {"transformedGatewayResponse": {"body": encoded}},
    }


# ---------------------------------------------------------------------------
# MCP target helpers
# ---------------------------------------------------------------------------

def mcp_request_passthrough(body: dict) -> dict:
    return {
        "interceptorOutputVersion": "1.0",
        "mcp": {"transformedGatewayRequest": {"body": body}},
    }


def mcp_response_passthrough(body: dict, status_code: int = 200) -> dict:
    return {
        "interceptorOutputVersion": "1.0",
        "mcp": {"transformedGatewayResponse": {"body": body, "statusCode": status_code}},
    }


def mcp_block(rpc_id, message: str) -> dict:
    """Return a JSON-RPC 2.0 error response for a blocked MCP call."""
    return {
        "interceptorOutputVersion": "1.0",
        "mcp": {
            "transformedGatewayResponse": {
                "statusCode": 200,  # JSON-RPC errors are delivered over HTTP 200
                "body": {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32000, "message": message},
                },
            }
        },
    }


def mcp_error(rpc_id, message: str = "Internal error during content inspection") -> dict:
    return {
        "interceptorOutputVersion": "1.0",
        "mcp": {
            "transformedGatewayResponse": {
                "statusCode": 500,
                "body": {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32603, "message": message},  # -32603 = Internal error
                },
            }
        },
    }


def mcp_transformed_request(new_body: dict) -> dict:
    return {
        "interceptorOutputVersion": "1.0",
        "mcp": {"transformedGatewayRequest": {"body": new_body}},
    }


def mcp_transformed_response(new_body: dict) -> dict:
    return {
        "interceptorOutputVersion": "1.0",
        "mcp": {"transformedGatewayResponse": {"body": new_body}},
    }
