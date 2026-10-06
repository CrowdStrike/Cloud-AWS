import pytest
from extractor import TextPart
from redactor import RedactionError, apply_redactions


def _parts(*pairs):
    return [TextPart(ptr, text, "user") for ptr, text in pairs]


def _msgs(*contents):
    return [{"role": "user", "content": c} for c in contents]


def test_single_redaction():
    body = {"messages": [{"role": "user", "content": "My SSN is 123-45-6789"}]}
    parts = _parts(("/messages/0/content", "My SSN is 123-45-6789"))
    new_msgs = _msgs("My SSN is *****6789")
    result = apply_redactions(body, parts, new_msgs)
    assert result["messages"][0]["content"] == "My SSN is *****6789"
    # Original body is not mutated
    assert body["messages"][0]["content"] == "My SSN is 123-45-6789"


def test_multi_part_redaction():
    body = {
        "contents": [
            {"parts": [{"text": "A"}, {"text": "B"}]}
        ]
    }
    parts = _parts(
        ("/contents/0/parts/0/text", "A"),
        ("/contents/0/parts/1/text", "B"),
    )
    result = apply_redactions(body, parts, _msgs("A-redacted", "B-redacted"))
    assert result["contents"][0]["parts"][0]["text"] == "A-redacted"
    assert result["contents"][0]["parts"][1]["text"] == "B-redacted"


def test_count_mismatch_raises():
    body = {"messages": [{"role": "user", "content": "Hi"}]}
    parts = _parts(("/messages/0/content", "Hi"))
    with pytest.raises(RedactionError, match="count mismatch"):
        apply_redactions(body, parts, [])


def test_bad_pointer_raises():
    body = {"messages": []}
    parts = _parts(("/messages/0/content", "Hi"))
    with pytest.raises(RedactionError):
        apply_redactions(body, parts, _msgs("Hi"))


def test_none_content_skipped():
    body = {"messages": [{"role": "user", "content": "original"}]}
    parts = _parts(("/messages/0/content", "original"))
    result = apply_redactions(body, parts, [{"role": "user", "content": None}])
    # None content means no change
    assert result["messages"][0]["content"] == "original"
