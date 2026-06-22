import json
from typing import Any

from openai import OpenAI


def _extract_json_block(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def parse_calendar_intent(
    api_key: str, model: str, user_message: str, timezone_name: str
) -> dict[str, Any]:
    client = OpenAI(api_key=api_key)
    prompt = f"""
You are a strict JSON intent parser for calendar actions.
User timezone: {timezone_name}
Return ONLY valid JSON with this schema:
{{
  "intent": "none|today|create|move|delete",
  "summary": "string or null",
  "start_iso": "ISO string or null",
  "end_iso": "ISO string or null",
  "event_id": "string or null",
  "needs_confirmation": true/false,
  "assistant_reply": "short user-facing text"
}}
Rules:
- If user asks to view today's schedule => intent "today".
- If unclear or missing required details => intent "none" and explain what's missing.
- For destructive action (delete) set needs_confirmation=true.
- For create/move, require explicit date+time, output local ISO offset when possible.
User message:
{user_message}
""".strip()

    response = client.responses.create(
        model=model,
        input=prompt,
        temperature=0,
    )

    text = response.output_text.strip()
    parsed = _extract_json_block(text)
    return parsed
