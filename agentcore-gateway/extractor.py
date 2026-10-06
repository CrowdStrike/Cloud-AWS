"""
Provider-native LLM body extractors.

Each extractor returns a list of TextPart objects — one per discrete text
field that should be inspected and potentially redacted by AIDR.  The
`pointer` field is an RFC 6901 JSON Pointer that locates the exact field in
the original body so AIDR-returned content can be written back surgically.

One TextPart per text field means AIDR can redact each field independently
without clobbering adjacent content.
"""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class TextPart:
    pointer: str   # RFC 6901 JSON Pointer into the original body
    text: str
    role: str      # "user", "assistant", or "system"


# ---------------------------------------------------------------------------
# Public dispatch
# ---------------------------------------------------------------------------

def extract(body: dict, provider: str) -> list[TextPart]:
    """Extract text parts from an LLM *request* body."""
    p = (provider or "openai").lower()
    if p == "anthropic":
        return _extract_anthropic(body)
    if p in ("openai", "azureai", "azure", "kong"):
        return _extract_openai(body)
    if p == "gemini":
        return _extract_gemini(body)
    if p == "cohere":
        return _extract_cohere(body)
    if p == "bedrock":
        return _extract_bedrock(body)
    return _extract_openai(body)


def extract_response(body: dict, provider: str) -> list[TextPart]:
    """Extract text parts from an LLM *response* body."""
    p = (provider or "openai").lower()
    if p == "anthropic":
        return _extract_anthropic_response(body)
    if p == "gemini":
        return _extract_gemini_response(body)
    if p == "cohere":
        return _extract_cohere_response(body)
    if p == "bedrock":
        return _extract_bedrock_response(body)
    return _extract_openai_response(body)


# ---------------------------------------------------------------------------
# OpenAI / Azure / Kong request
# ---------------------------------------------------------------------------

def _extract_openai(body: dict) -> list[TextPart]:
    parts: list[TextPart] = []

    # Chat Completions API: messages[]
    for i, msg in enumerate(body.get("messages", [])):
        role = msg.get("role", "user")
        content = msg.get("content")
        if content is None:
            continue
        if isinstance(content, str):
            if content:
                parts.append(TextPart(f"/messages/{i}/content", content, role))
        elif isinstance(content, list):
            for j, block in enumerate(content):
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        parts.append(TextPart(f"/messages/{i}/content/{j}/text", text, role))
                else:
                    # Unknown block — serialize and submit so the message isn't dropped
                    serialized = json.dumps(block)
                    if serialized:
                        parts.append(TextPart(f"/messages/{i}/content/{j}", serialized, role))

    # Responses API: input (string or message array)
    inp = body.get("input")
    if isinstance(inp, str):
        if inp:
            parts.append(TextPart("/input", inp, "user"))
    elif isinstance(inp, list):
        for i, msg in enumerate(inp):
            if not isinstance(msg, dict):
                continue
            role = msg.get("role", "user")
            content = msg.get("content")
            if content is None:
                continue
            if isinstance(content, str):
                if content:
                    parts.append(TextPart(f"/input/{i}/content", content, role))
            elif isinstance(content, list):
                for j, block in enumerate(content):
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") in ("input_text", "text"):
                        text = block.get("text", "")
                        if text:
                            parts.append(TextPart(f"/input/{i}/content/{j}/text", text, role))

    return parts


# ---------------------------------------------------------------------------
# Anthropic request
# ---------------------------------------------------------------------------

def _flatten_anthropic_block(block: dict) -> str | None:
    """Recursively flatten an Anthropic content block to plain text."""
    t = block.get("type")
    if t == "text":
        return block.get("text")
    if t == "input_text":
        return block.get("input_text")
    if t == "tool_result":
        nested = block.get("content", [])
        if isinstance(nested, list):
            texts = [_flatten_anthropic_block(b) for b in nested if isinstance(b, dict)]
            texts = [x for x in texts if x]
            return "\n".join(texts) if texts else None
    if t == "document":
        return (block.get("source") or {}).get("data")
    if "text" in block:
        return block["text"]
    return None


def _extract_anthropic(body: dict) -> list[TextPart]:
    parts: list[TextPart] = []

    # system — string or array of text blocks
    system = body.get("system")
    if isinstance(system, str):
        if system:
            parts.append(TextPart("/system", system, "system"))
    elif isinstance(system, list):
        for j, block in enumerate(system):
            if isinstance(block, dict):
                text = block.get("text", "")
                if text:
                    parts.append(TextPart(f"/system/{j}/text", text, "system"))

    # messages
    for i, msg in enumerate(body.get("messages", [])):
        role = msg.get("role", "user")
        content = msg.get("content")
        if content is None:
            continue
        if isinstance(content, str):
            if content:
                parts.append(TextPart(f"/messages/{i}/content", content, role))
        elif isinstance(content, list):
            for j, block in enumerate(content):
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        parts.append(TextPart(f"/messages/{i}/content/{j}/text", text, role))
                else:
                    flat = _flatten_anthropic_block(block)
                    if flat is None:
                        flat = json.dumps(block)
                    if flat:
                        parts.append(TextPart(f"/messages/{i}/content/{j}", flat, role))

    return parts


# ---------------------------------------------------------------------------
# Gemini request
# ---------------------------------------------------------------------------

def _extract_gemini(body: dict) -> list[TextPart]:
    parts: list[TextPart] = []

    # systemInstruction.parts[].text
    si = body.get("systemInstruction")
    if isinstance(si, dict):
        for j, part in enumerate(si.get("parts", [])):
            if isinstance(part, dict):
                text = part.get("text", "")
                if text:
                    parts.append(TextPart(f"/systemInstruction/parts/{j}/text", text, "system"))

    # contents[].parts[].text
    for i, content in enumerate(body.get("contents", [])):
        if not isinstance(content, dict):
            continue
        raw_role = content.get("role", "user")
        role = "assistant" if raw_role == "model" else raw_role
        for j, part in enumerate(content.get("parts", [])):
            if isinstance(part, dict):
                text = part.get("text", "")
                if text:
                    parts.append(TextPart(f"/contents/{i}/parts/{j}/text", text, role))

    return parts


# ---------------------------------------------------------------------------
# Cohere request
# ---------------------------------------------------------------------------

def _extract_cohere(body: dict) -> list[TextPart]:
    # Cohere v2: messages[] — same schema as OpenAI
    if "messages" in body:
        return _extract_openai(body)

    # Cohere v1: message + chat_history
    parts: list[TextPart] = []
    message = body.get("message", "")
    if message:
        parts.append(TextPart("/message", message, "user"))

    for i, entry in enumerate(body.get("chat_history", [])):
        if not isinstance(entry, dict):
            continue
        raw_role = entry.get("role", "USER").upper()
        role = "assistant" if raw_role == "CHATBOT" else raw_role.lower()
        text = entry.get("message", "")
        if text:
            parts.append(TextPart(f"/chat_history/{i}/message", text, role))

    return parts


# ---------------------------------------------------------------------------
# Bedrock request (Converse + InvokeModel)
# ---------------------------------------------------------------------------

def _extract_bedrock(body: dict) -> list[TextPart]:
    parts: list[TextPart] = []

    # Bedrock Converse: system[] + messages[].content[].text
    if "messages" in body:
        for j, block in enumerate(body.get("system", [])):
            if isinstance(block, dict):
                text = block.get("text", "")
                if text:
                    parts.append(TextPart(f"/system/{j}/text", text, "system"))

        for i, msg in enumerate(body.get("messages", [])):
            role = msg.get("role", "user")
            for k, block in enumerate(msg.get("content", [])):
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        parts.append(TextPart(f"/messages/{i}/content/{k}/text", text, role))
                else:
                    text = block.get("text") or json.dumps(block)
                    if text:
                        parts.append(TextPart(f"/messages/{i}/content/{k}", text, role))
        return parts

    # Bedrock InvokeModel — Titan
    if "inputText" in body:
        text = body.get("inputText", "")
        if text:
            parts.append(TextPart("/inputText", text, "user"))
        return parts

    # Bedrock InvokeModel — Llama
    if "prompt" in body:
        text = body.get("prompt", "")
        if text:
            parts.append(TextPart("/prompt", text, "user"))

    return parts


# ---------------------------------------------------------------------------
# Response extractors
# ---------------------------------------------------------------------------

def _extract_openai_response(body: dict) -> list[TextPart]:
    parts: list[TextPart] = []

    # Chat Completions: choices[]
    for i, choice in enumerate(body.get("choices", [])):
        message = choice.get("message", {})
        content = message.get("content")
        role = message.get("role", "assistant")
        if content is None:
            continue
        if isinstance(content, str):
            if content:
                parts.append(TextPart(f"/choices/{i}/message/content", content, role))
        elif isinstance(content, list):
            for j, block in enumerate(content):
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        parts.append(TextPart(f"/choices/{i}/message/content/{j}/text", text, role))

    # Responses API: output[].content[].text (type=output_text)
    for i, item in enumerate(body.get("output", [])):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        role = item.get("role", "assistant")
        for j, block in enumerate(item.get("content", [])):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "output_text":
                text = block.get("text", "")
                if text:
                    parts.append(TextPart(f"/output/{i}/content/{j}/text", text, role))

    return parts


def _extract_anthropic_response(body: dict) -> list[TextPart]:
    parts: list[TextPart] = []
    for i, block in enumerate(body.get("content", [])):
        if isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text", "")
            if text:
                parts.append(TextPart(f"/content/{i}/text", text, "assistant"))
    return parts


def _extract_gemini_response(body: dict) -> list[TextPart]:
    parts: list[TextPart] = []
    for i, candidate in enumerate(body.get("candidates", [])):
        content = candidate.get("content", {})
        for j, part in enumerate(content.get("parts", [])):
            if isinstance(part, dict):
                text = part.get("text", "")
                if text:
                    parts.append(TextPart(f"/candidates/{i}/content/parts/{j}/text", text, "assistant"))
    return parts


def _extract_cohere_response(body: dict) -> list[TextPart]:
    parts: list[TextPart] = []
    # Cohere v1: top-level text field
    text = body.get("text", "")
    if text:
        parts.append(TextPart("/text", text, "assistant"))
    # Cohere v2: message.content[]
    message = body.get("message", {})
    if isinstance(message, dict):
        for i, block in enumerate(message.get("content", [])):
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text", "")
                if t:
                    parts.append(TextPart(f"/message/content/{i}/text", t, "assistant"))
    return parts


def _extract_bedrock_response(body: dict) -> list[TextPart]:
    parts: list[TextPart] = []
    # Bedrock Converse: output.message.content[].text
    output = body.get("output", {})
    if isinstance(output, dict):
        message = output.get("message", {})
        if isinstance(message, dict):
            for k, block in enumerate(message.get("content", [])):
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        parts.append(TextPart(f"/output/message/content/{k}/text", text, "assistant"))
    # Bedrock InvokeModel Titan: results[].outputText
    for i, result in enumerate(body.get("results", [])):
        if isinstance(result, dict):
            text = result.get("outputText", "")
            if text:
                parts.append(TextPart(f"/results/{i}/outputText", text, "assistant"))
    # Bedrock InvokeModel Llama: generation
    generation = body.get("generation", "")
    if generation:
        parts.append(TextPart("/generation", generation, "assistant"))
    return parts
