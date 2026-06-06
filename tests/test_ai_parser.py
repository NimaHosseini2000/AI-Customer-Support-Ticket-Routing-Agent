import json

import pytest

from app.services.ai_service import parse_ai_response

_VALID_PAYLOAD = {
    "category": "Billing",
    "priority": "High",
    "summary": "Customer reports a double charge.",
    "suggested_response": "We will investigate the billing issue immediately.",
}
_VALID_JSON = json.dumps(_VALID_PAYLOAD)


def test_valid_json_parses_correctly():
    result = parse_ai_response(_VALID_JSON)
    assert result == _VALID_PAYLOAD


def test_json_inside_markdown_fence_parses_correctly():
    text = f"```json\n{_VALID_JSON}\n```"
    result = parse_ai_response(text)
    assert result["category"] == "Billing"
    assert result["priority"] == "High"


def test_json_inside_plain_code_fence_parses_correctly():
    text = f"```\n{_VALID_JSON}\n```"
    result = parse_ai_response(text)
    assert result["summary"] == _VALID_PAYLOAD["summary"]


def test_json_embedded_in_prose_parses_correctly():
    text = f"Here is the analysis:\n{_VALID_JSON}\nEnd of analysis."
    result = parse_ai_response(text)
    assert result["priority"] == "High"


def test_invalid_json_raises_value_error():
    with pytest.raises(ValueError, match="Could not parse AI response"):
        parse_ai_response("This is completely invalid text with no JSON.")


def test_malformed_json_object_raises_value_error():
    with pytest.raises(ValueError):
        parse_ai_response("{category: Billing, priority: High}")
