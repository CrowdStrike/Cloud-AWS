"""
MCP (Model Context Protocol) JSON-RPC 2.0 target interceptor.

REQUEST phase: inspect tools/call arguments as event_type=tool_input.
RESPONSE phase: inspect tools/list tool definitions as event_type=tool_listing.
All other MCP methods pass through uninspected.

Unlike HTTP targets, MCP bodies arrive as parsed JSON dicts (no base64),
so no codec is needed.
"""

from __future__ import annotations

import json
import logging
import os

import aidr_client
from decision import mcp_block, mcp_error, mcp_request_passthrough, mcp_response_passthrough

logger = logging.getLogger(__name__)

_FAIL_OPEN = os.environ.get("AIDR_FAIL_OPEN", "false").lower() == "true"

# Methods that carry no inspectable content and should pass through immediately.
_PASSTHROUGH_METHODS = {
    "initialize",
    "ping",
    "notifications/initialized",
    "notifications/cancelled",
    "notifications/progress",
    "notifications/message",
    "notifications/resources/updated",
    "notifications/resources/list_changed",
    "notifications/tools/list_changed",
    "notifications/prompts/list_changed",
}


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def handle_request(event: dict, context) -> dict:
    mcp = event["mcp"]
    body = (mcp.get("gatewayRequest") or {}).get("body", {})

    method = body.get("method", "")
    rpc_id = body.get("id")

    if method in _PASSTHROUGH_METHODS:
        return mcp_request_passthrough(body)

    if method == "tools/call":
        return _tools_call(body, rpc_id, context)

    return mcp_request_passthrough(body)


def handle_response(event: dict, context) -> dict:
    mcp = event["mcp"]
    req_body = (mcp.get("gatewayRequest") or {}).get("body", {})
    resp = mcp.get("gatewayResponse") or {}
    resp_body = resp.get("body", {})
    resp_status = resp.get("statusCode", 200)

    method = req_body.get("method", "")
    rpc_id = req_body.get("id")

    if method == "tools/list":
        return _tools_list(resp_body, rpc_id, resp_status, context)

    return mcp_response_passthrough(resp_body, resp_status)


# ---------------------------------------------------------------------------
# Per-method handlers
# ---------------------------------------------------------------------------

def _tools_call(body: dict, rpc_id, context) -> dict:
    params = body.get("params", {})
    tool_name = params.get("name", "unknown")
    arguments = params.get("arguments") or {}

    content = json.dumps(arguments) if arguments else ""
    if not content:
        return mcp_request_passthrough(body)

    try:
        aidr_resp = aidr_client.call_aidr(
            event_type="tool_input",
            guard_input={"messages": [{"role": "user", "content": content}]},
            source_ip=_source_ip(context),
            source_location=_gateway_arn(context),
            **_static_meta(),
        )
    except aidr_client.AIDRUnreachableError as exc:
        logger.error("AIDR unreachable on tools/call: %s", exc)
        return mcp_request_passthrough(body) if _FAIL_OPEN else mcp_error(rpc_id)

    result = aidr_resp.get("result") or {}
    if result.get("blocked"):
        reason = aidr_resp.get("summary") or "Tool call blocked by CrowdStrike AIDR policy"
        logger.info("AIDR: decision=BLOCKED event_type=tool_input tool=%s", tool_name)
        return mcp_block(rpc_id, reason)

    logger.info("AIDR: decision=ALLOWED event_type=tool_input tool=%s", tool_name)
    return mcp_request_passthrough(body)


def _tools_list(resp_body: dict, rpc_id, resp_status: int, context) -> dict:
    tools = (resp_body.get("result") or {}).get("tools", [])
    if not tools:
        return mcp_response_passthrough(resp_body, resp_status)

    aidr_tools = [
        {
            "type": "function",
            "function": {
                "name": t.get("name", ""),
                "description": t.get("description", ""),
                "parameters": t.get("inputSchema", {}),
            },
        }
        for t in tools
    ]

    try:
        aidr_resp = aidr_client.call_aidr(
            event_type="tool_listing",
            guard_input={"tools": aidr_tools},
            source_ip=_source_ip(context),
            source_location=_gateway_arn(context),
            **_static_meta(),
        )
    except aidr_client.AIDRUnreachableError as exc:
        logger.error("AIDR unreachable on tools/list: %s", exc)
        return mcp_response_passthrough(resp_body, resp_status) if _FAIL_OPEN else mcp_error(rpc_id)

    result = aidr_resp.get("result") or {}
    if result.get("blocked"):
        reason = aidr_resp.get("summary") or "Tool listing blocked by CrowdStrike AIDR policy"
        logger.info("AIDR: decision=BLOCKED event_type=tool_listing")
        return mcp_block(rpc_id, reason)

    logger.info("AIDR: decision=ALLOWED event_type=tool_listing")
    return mcp_response_passthrough(resp_body, resp_status)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _static_meta() -> dict:
    return {k: v for k, v in {
        "app_id": os.environ.get("AIDR_APP_ID"),
        "collector_instance_id": os.environ.get("AIDR_COLLECTOR_INSTANCE_ID"),
    }.items() if v}


def _source_ip(context) -> str | None:
    try:
        return context.client_context.custom.get("SOURCE_IP")
    except AttributeError:
        return None


def _gateway_arn(context) -> str | None:
    try:
        return context.client_context.custom.get("GATEWAY_ARN")
    except AttributeError:
        return None
