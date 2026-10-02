"""
HTTP / inference target interceptor.

REQUEST phase: decode body → extract provider-native text parts → call AIDR →
  block / transform / allow.  Saves request context to DynamoDB for the
  response phase.

RESPONSE phase: load request context → extract response text parts → call AIDR
  → block / transform / allow.
"""

from __future__ import annotations

import logging
import os

import aidr_client
import state_store
from codec import decode_body, encode_body
from decision import (
    http_block, http_error, http_passthrough,
    http_transformed_request, http_transformed_response,
)
from extractor import TextPart, extract, extract_response
from redactor import RedactionError, apply_redactions

logger = logging.getLogger(__name__)

_FAIL_OPEN = os.environ.get("AIDR_FAIL_OPEN", "false").lower() == "true"
_INSPECT_METHODS = {"POST", "PUT", "PATCH"}


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def handle_request(event: dict, context) -> dict:
    http = event["http"]
    request = http.get("gatewayRequest", {})

    method = request.get("httpMethod", "POST").upper()
    if method not in _INSPECT_METHODS:
        return http_passthrough()

    body, is_json = decode_body(request.get("body", ""))
    if not is_json:
        return http_passthrough()

    headers = request.get("headers", {})
    path = request.get("path", "")
    provider = _resolve_provider(path, headers, body)
    text_parts: list[TextPart] = extract(body, provider)
    if not text_parts:
        return http_passthrough()

    request_id = _request_id(context)
    state_store.save(request_id, {
        "provider": provider,
        "user_id": _header(headers, "x-aidr-user-id") or os.environ.get("AIDR_USER_ID"),
        "tenant_id": _header(headers, "x-aidr-tenant-id") or os.environ.get("AIDR_TENANT_ID"),
        "model": _infer_model(body),
        "llm_provider_display": _provider_display(provider),
    })

    try:
        aidr_resp = aidr_client.call_aidr(
            event_type="input",
            guard_input={"messages": [{"role": p.role, "content": p.text} for p in text_parts]},
            source_ip=_source_ip(context),
            source_location=_gateway_arn(context),
            user_id=_header(headers, "x-aidr-user-id") or os.environ.get("AIDR_USER_ID"),
            tenant_id=_header(headers, "x-aidr-tenant-id") or os.environ.get("AIDR_TENANT_ID"),
            model=_infer_model(body),
            llm_provider=_provider_display(provider),
            **_static_meta(),
        )
    except aidr_client.AIDRUnreachableError as exc:
        logger.error("AIDR unreachable on request: %s", exc)
        state_store.delete(request_id)
        return http_passthrough() if _FAIL_OPEN else http_error()

    result = aidr_resp.get("result") or {}

    if result.get("blocked"):
        reason = aidr_resp.get("summary") or "Content blocked by CrowdStrike AIDR policy"
        logger.info("AIDR: decision=BLOCKED event_type=input")
        state_store.delete(request_id)
        return http_block(400, reason)

    if result.get("transformed"):
        new_msgs = (result.get("guard_output") or {}).get("messages") or []
        if new_msgs:
            try:
                new_body = apply_redactions(body, text_parts, new_msgs)
            except RedactionError as exc:
                logger.error("AIDR: apply_redactions failed: %s; blocking request", exc)
                state_store.delete(request_id)
                return http_error()
            logger.info("AIDR: decision=TRANSFORMED event_type=input")
            return http_transformed_request(new_body)

    logger.info("AIDR: decision=ALLOWED event_type=input")
    return http_passthrough()


def handle_response(event: dict, context) -> dict:
    http = event["http"]
    response = http.get("gatewayResponse") or {}

    # Streaming responses are not supported by the interceptor — pass through.
    if response.get("isStreamingResponse"):
        return http_passthrough()

    body, is_json = decode_body(response.get("body", ""))
    if not is_json:
        return http_passthrough()

    request_id = _request_id(context)
    req_ctx = state_store.load(request_id) or {}
    state_store.delete(request_id)

    provider = req_ctx.get("provider", os.environ.get("AIDR_LLM_PROVIDER", "openai"))
    text_parts: list[TextPart] = extract_response(body, provider)
    if not text_parts:
        return http_passthrough()

    try:
        aidr_resp = aidr_client.call_aidr(
            event_type="output",
            guard_input={"messages": [{"role": p.role, "content": p.text} for p in text_parts]},
            source_ip=_source_ip(context),
            source_location=_gateway_arn(context),
            user_id=req_ctx.get("user_id"),
            tenant_id=req_ctx.get("tenant_id"),
            model=req_ctx.get("model"),
            llm_provider=req_ctx.get("llm_provider_display"),
            **_static_meta(),
        )
    except aidr_client.AIDRUnreachableError as exc:
        logger.error("AIDR unreachable on response: %s", exc)
        return http_passthrough() if _FAIL_OPEN else http_error()

    result = aidr_resp.get("result") or {}

    if result.get("blocked"):
        reason = aidr_resp.get("summary") or "Response blocked by CrowdStrike AIDR policy"
        logger.info("AIDR: decision=BLOCKED event_type=output")
        return http_block(400, reason)

    if result.get("transformed"):
        new_msgs = (result.get("guard_output") or {}).get("messages") or []
        if new_msgs:
            try:
                new_body = apply_redactions(body, text_parts, new_msgs)
            except RedactionError as exc:
                logger.error("AIDR: apply_redactions failed: %s; blocking response", exc)
                return http_error()
            logger.info("AIDR: decision=TRANSFORMED event_type=output")
            return http_transformed_response(new_body)

    logger.info("AIDR: decision=ALLOWED event_type=output")
    return http_passthrough()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_provider(path: str, headers: dict, body: dict) -> str:
    """
    Resolve LLM provider.  Priority: explicit env var → path heuristic → body
    heuristic → default (openai).
    """
    explicit = os.environ.get("AIDR_LLM_PROVIDER", "").lower()
    if explicit:
        return explicit
    lp = path.lower()
    if "anthropic" in lp or body.get("anthropic_version"):
        return "anthropic"
    if "gemini" in lp or "generatecontent" in lp or "contents" in body:
        return "gemini"
    if "cohere" in lp:
        return "cohere"
    if "bedrock" in lp or "converse" in lp or "inputText" in body or "prompt" in body:
        return "bedrock"
    return "openai"


_PROVIDER_DISPLAY = {
    "openai": "OpenAI", "azureai": "Azure OpenAI", "azure": "Azure OpenAI",
    "anthropic": "Anthropic", "bedrock": "AWS Bedrock",
    "cohere": "Cohere", "gemini": "Google Gemini",
}


def _provider_display(provider: str) -> str:
    return _PROVIDER_DISPLAY.get(provider, provider)


def _infer_model(body: dict) -> str | None:
    return body.get("model") or body.get("modelId") or os.environ.get("AIDR_MODEL")


def _header(headers: dict, name: str) -> str | None:
    return headers.get(name) or headers.get(name.lower())


def _static_meta() -> dict:
    return {k: v for k, v in {
        "app_id": os.environ.get("AIDR_APP_ID"),
        "collector_instance_id": os.environ.get("AIDR_COLLECTOR_INSTANCE_ID"),
    }.items() if v}


def _request_id(context) -> str:
    try:
        return context.client_context.custom.get("REQUEST_ID") or context.aws_request_id
    except AttributeError:
        return context.aws_request_id


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
