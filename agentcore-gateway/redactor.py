"""
Apply AIDR-returned redactions back into the original body using RFC 6901
JSON Pointers.

Fail-closed: any mismatch or pointer resolution failure raises RedactionError,
which callers must handle by blocking the request/response rather than passing
unredacted content through.

RFC 6901 pointer resolution is implemented inline — no external dependencies.
"""

from __future__ import annotations

import copy

from extractor import TextPart


class RedactionError(Exception):
    pass


def _pointer_set(doc: dict | list, pointer: str, value) -> None:
    """
    Set the value at an RFC 6901 JSON Pointer location within doc (in place).

    Raises RedactionError if any path segment cannot be resolved.
    """
    if not pointer.startswith("/"):
        raise RedactionError(f"Invalid JSON Pointer (must start with /): {pointer!r}")

    # Split and unescape: ~1 → /  then  ~0 → ~  (order matters per spec)
    parts = [p.replace("~1", "/").replace("~0", "~") for p in pointer[1:].split("/")]

    target = doc
    for segment in parts[:-1]:
        if isinstance(target, dict):
            if segment not in target:
                raise RedactionError(f"Key {segment!r} not found in object at pointer {pointer!r}")
            target = target[segment]
        elif isinstance(target, list):
            try:
                target = target[int(segment)]
            except (ValueError, IndexError) as exc:
                raise RedactionError(
                    f"Invalid list index {segment!r} at pointer {pointer!r}: {exc}"
                ) from exc
        else:
            raise RedactionError(
                f"Cannot traverse into {type(target).__name__} at pointer {pointer!r}"
            )

    last = parts[-1]
    if isinstance(target, dict):
        if last not in target:
            raise RedactionError(f"Key {last!r} not found at pointer {pointer!r}")
        target[last] = value
    elif isinstance(target, list):
        try:
            target[int(last)] = value
        except (ValueError, IndexError) as exc:
            raise RedactionError(
                f"Invalid list index {last!r} at pointer {pointer!r}: {exc}"
            ) from exc
    else:
        raise RedactionError(
            f"Cannot set on {type(target).__name__} at pointer {pointer!r}"
        )


def apply_redactions(body: dict, text_parts: list[TextPart], new_messages: list[dict]) -> dict:
    """
    Write AIDR-returned content back into `body` at the pointer for each TextPart.

    `text_parts` and `new_messages` must have the same length — they are the
    messages we sent to AIDR and the (possibly redacted) messages AIDR returned,
    in the same order.

    Returns a deep copy of `body` with redactions applied.
    Raises RedactionError on count mismatch or pointer resolution failure.
    """
    if len(new_messages) != len(text_parts):
        raise RedactionError(
            f"Redaction count mismatch: sent {len(text_parts)} messages, "
            f"received {len(new_messages)}"
        )

    result = copy.deepcopy(body)

    for part, new_msg in zip(text_parts, new_messages):
        content = new_msg.get("content")
        if content is None:
            continue
        _pointer_set(result, part.pointer, content)

    return result
