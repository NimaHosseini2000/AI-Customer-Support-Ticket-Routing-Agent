import json
import os
import re

from openai import APIError, OpenAI

_SYSTEM_PROMPT = """\
You are a customer support ticket classifier. Analyze the customer message and return a JSON response.

Allowed categories (choose exactly one):
- Billing
- Technical
- Account Access
- Feature Request
- General Inquiry

Allowed priorities (choose exactly one):
- High
- Medium
- Low

Return ONLY valid JSON in this exact format:
{
  "category": "<category>",
  "priority": "<priority>",
  "summary": "<one-sentence summary of the issue>",
  "suggested_response": "<professional response draft to send to the customer>"
}"""


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


_REQUIRED_KEYS = {"category", "priority", "summary", "suggested_response"}


def _validate(parsed: dict) -> dict:
    missing = _REQUIRED_KEYS - parsed.keys()
    if missing:
        raise ValueError(
            f"AI response missing required fields: {sorted(missing)}. "
            f"Keys received: {sorted(parsed.keys())}"
        )
    return parsed


def parse_ai_response(text: str) -> dict:
    """Extract, parse, and validate JSON from the AI response text."""
    try:
        return _validate(json.loads(text))
    except json.JSONDecodeError:
        pass

    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if code_block:
        try:
            return _validate(json.loads(code_block.group(1)))
        except json.JSONDecodeError:
            pass

    json_object = re.search(r"\{[\s\S]*\}", text)
    if json_object:
        try:
            return _validate(json.loads(json_object.group(0)))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse AI response as JSON. Response was: {text[:300]!r}")


def analyze_ticket(message: str, customer_plan: str, customer_status: str) -> dict:
    """Classify and analyze a support ticket using OpenAI."""
    client = _get_client()

    user_content = (
        f"Customer Plan: {customer_plan}\n"
        f"Customer Status: {customer_status}\n"
        f"Customer Message: {message}"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
    except APIError as exc:
        raise RuntimeError(f"OpenAI API error: {exc}") from exc

    content = completion.choices[0].message.content or ""
    return parse_ai_response(content)
