import asyncio
import json

from anthropic import Anthropic

from .constants import MODEL
from .prompts import EXTRACT_SYSTEM, NEXT_TRIP_SYSTEM, SELECT_SYSTEM
from .utils import response_text, safe_json_parse


client = Anthropic()


def _extract_sync(user_text: str) -> dict:
    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        temperature=0,
        system=EXTRACT_SYSTEM,
        messages=[{"role": "user", "content": user_text}],
    )
    return safe_json_parse(response_text(response))


async def extract_trip_request(user_text: str) -> dict:
    return await asyncio.to_thread(_extract_sync, user_text)


def _select_sync(req: dict, options: dict, hint: str = "") -> dict:
    llm_options = {key: value for key, value in options.items() if key not in {"pharmacy", "activities", "transfers"}}
    payload = {"trip": req, "options": llm_options}
    user_text = json.dumps(payload, ensure_ascii=False, indent=2)

    if hint:
        user_text += f"\n\nВажно: {hint}"

    response = client.messages.create(
        model=MODEL,
        max_tokens=600,
        temperature=0.2,
        system=SELECT_SYSTEM,
        messages=[{"role": "user", "content": user_text}],
    )

    return safe_json_parse(response_text(response))


async def select_options(req: dict, options: dict, hint: str = "") -> dict:
    return await asyncio.to_thread(_select_sync, req, options, hint)


def _suggest_next_trip_sync(plan: dict) -> dict:
    user_text = json.dumps({"current_plan": plan}, ensure_ascii=False, indent=2)

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        temperature=0.3,
        system=NEXT_TRIP_SYSTEM,
        messages=[{"role": "user", "content": user_text}],
    )

    return safe_json_parse(response_text(response))


async def suggest_next_trip(plan: dict) -> dict:
    return await asyncio.to_thread(_suggest_next_trip_sync, plan)
