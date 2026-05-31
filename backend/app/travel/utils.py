import json
from typing import Any


def safe_json_parse(raw: str) -> dict:
    text = raw.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    last = max(text.rfind("}"), text.rfind("]"))
    if last != -1:
        text = text[:last + 1]

    return json.loads(text)


def response_text(response: Any) -> str:
    content = getattr(response, "content", [])
    if not content:
        return ""

    first = content[0]
    return getattr(first, "text", str(first))


def selection_body(selection: dict) -> dict:
    body = selection.get("selection", selection)
    return body if isinstance(body, dict) else {}


def choice_ids(choice: Any) -> list[str]:
    if choice is None:
        return []

    if isinstance(choice, list):
        return [
            str(item["id"])
            for item in choice
            if isinstance(item, dict) and item.get("id")
        ]

    if isinstance(choice, dict) and choice.get("id"):
        return [str(choice["id"])]

    if isinstance(choice, str):
        return [choice]

    return []


def first_choice_id(choice: Any) -> str | None:
    ids = choice_ids(choice)
    return ids[0] if ids else None
