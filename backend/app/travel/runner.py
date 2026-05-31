import asyncio
from datetime import date, timedelta

from .assembler import assemble_plan
from .clarifier import apply_quick_reply, build_clarification, merge_requests
from .constants import DEFAULTS, VALID_NEEDS
from .date_utils import normalize_trip_dates
from .evaluator import evaluate_plan
from .llm import extract_trip_request
from .mock_repo import fetch_options
from .plan_modifier import (
    add_activity_to_plan,
    add_restaurant_to_plan,
    detect_modification_intent,
    remove_category_from_plan,
)
from .plan_store import save_plan
from .prefilter import prefilter_options
from .security import mask_pii, sanitize_user_input
from .selector import build_selection
from .weather import get_weather_for_dates


def validate_and_fill_defaults(req: dict) -> tuple[dict, str | None]:
    filled = dict(req)

    for key, value in DEFAULTS.items():
        if filled.get(key) is None:
            filled[key] = value

    if filled.get("dates") is None:
        filled["dates"] = "выходные"

    if filled.get("pax") is not None:
        try:
            filled["pax"] = max(1, int(filled["pax"]))
        except (TypeError, ValueError):
            filled["pax"] = None

    try:
        filled["nights"] = max(1, int(filled["nights"]))
    except (TypeError, ValueError):
        filled["nights"] = DEFAULTS["nights"]

    if filled.get("budget") is not None:
        try:
            filled["budget"] = max(0, int(filled["budget"]))
        except (TypeError, ValueError):
            filled["budget"] = None

    needs = filled.get("needs") or DEFAULTS["needs"]
    filled["needs"] = [need for need in needs if need in VALID_NEEDS]
    if not filled["needs"]:
        filled["needs"] = DEFAULTS["needs"]

    # insurance is always included
    if "insurance" not in filled["needs"]:
        filled["needs"].append("insurance")

    # activity, transfer, restaurant always included
    for auto_need in ("activity", "transfer", "restaurant"):
        if auto_need not in filled["needs"]:
            filled["needs"].append(auto_need)

    # solo trip should not be family_weekend
    if int(filled.get("pax") or 1) == 1 and filled.get("trip_type") == "family_weekend":
        filled["trip_type"] = "leisure"

    filled = normalize_family_members(filled)
    filled = normalize_needs(filled)
    return filled, None


def normalize_family_members(req: dict) -> dict:
    members = req.get("family_members")
    if not members:
        return req

    normalized = []
    for member in members or []:
        if not isinstance(member, dict):
            continue
        role = str(member.get("role") or "взрослый").strip().lower()
        if role in {"сын", "дочь", "мальчик", "девочка", "child", "kid", "ребёнок", "ребенок", "СЂРµР±С‘РЅРѕРє"}:
            role = "ребёнок"
        elif role in {"жена", "мама", "mother", "РјР°РјР°"}:
            role = "мама"
        elif role in {"муж", "папа", "father", "РїР°РїР°"}:
            role = "папа"
        elif role not in {"папа", "мама", "ребёнок", "взрослый"}:
            role = "взрослый"

        try:
            age = member.get("age")
            age = int(age) if age is not None else None
        except (TypeError, ValueError):
            age = None

        normalized.append({"role": role, "age": age, "name": member.get("name")})

    req["family_members"] = normalized
    return req


def normalize_needs(req: dict) -> dict:
    needs = list(req.get("needs") or DEFAULTS["needs"])
    members = req.get("family_members") or []
    has_kids = any(_is_child_role(member.get("role")) for member in members if isinstance(member, dict))
    if has_kids and "pharmacy" not in needs:
        needs.append("pharmacy")
    if not has_kids and "pharmacy" in needs:
        needs = [need for need in needs if need != "pharmacy"]
    req["needs"] = needs
    return req


def _is_child_role(role: str | None) -> bool:
    return str(role or "").strip().lower() in {"ребёнок", "ребенок", "child", "kid", "СЂРµР±С‘РЅРѕРє"}


async def emit(stream, step: str, icon: str, text: str, done: bool = False):
    msg = {
        "type": "thinking",
        "step": step,
        "icon": icon,
        "text": text,
        "status": "done" if done else "in_progress",
    }

    print(f"{icon} [{step.upper()}] {text}")

    if stream:
        try:
            await stream.send_json(msg)
        except Exception:
            pass


async def send_error(stream, text: str, reason: str | None = None) -> dict:
    result = {
        "status": "error",
        "error": text,
        "reason": reason,
        "can_book": False,
    }

    if stream:
        try:
            await stream.send_json({"type": "error", "text": text, "reason": reason})
        except Exception:
            pass

    return result


async def wait_with_keepalive(awaitable, stream):
    task = asyncio.create_task(awaitable)

    while not task.done():
        await asyncio.sleep(1.5)
        if task.done() or not stream:
            continue
        try:
            await stream.send_json({"type": "ping"})
        except Exception:
            pass

    return await task


async def run_workflow(user_text: str, stream=None, partial_request=None, current_plan: dict | None = None) -> dict:
    await emit(stream, "extract", "🔍", "Анализирую запрос...")

    clean_text, is_suspicious = sanitize_user_input(user_text)
    if is_suspicious:
        return await send_error(
            stream,
            "Не смог разобрать запрос. Напиши проще: куда, когда и сколько человек.",
        )

    masked_text = mask_pii(clean_text)

    try:
        req = await wait_with_keepalive(extract_trip_request(masked_text), stream)
    except Exception as exc:
        return await send_error(stream, f"Не удалось разобрать запрос: {exc}")

    if partial_request:
        req = merge_requests(partial_request, req)
        req = apply_quick_reply(clean_text, req)

    req, error = validate_and_fill_defaults(req)

    if error:
        return await send_error(stream, error)

    # Normalize trip dates (fills start_date/end_date/nights/days from text)
    req = normalize_trip_dates(req)

    # Handle modification intents when a current plan exists
    if current_plan:
        intent = detect_modification_intent(clean_text)
        if intent == "add_activity":
            options = fetch_options(req)
            candidates = prefilter_options(req, options)
            plan = add_activity_to_plan(current_plan, req, candidates)
            save_plan(plan)
            if stream:
                try:
                    await stream.send_json({"type": "plan_ready", "plan": plan})
                except Exception:
                    pass
            return plan
        elif intent == "add_restaurant":
            options = fetch_options(req)
            candidates = prefilter_options(req, options)
            plan = add_restaurant_to_plan(current_plan, req, candidates)
            save_plan(plan)
            if stream:
                try:
                    await stream.send_json({"type": "plan_ready", "plan": plan})
                except Exception:
                    pass
            return plan
        elif intent == "remove_pharmacy":
            plan = remove_category_from_plan(current_plan, "travel_kit")
            save_plan(plan)
            if stream:
                try:
                    await stream.send_json({"type": "plan_ready", "plan": plan})
                except Exception:
                    pass
            return plan

    clarification = build_clarification(req)
    if clarification:
        if stream:
            await stream.send_json({"type": "need_clarification", **clarification})
        return clarification

    await emit(
        stream,
        "extract",
        "🔍",
        f"→ to_city={req['to_city']}, pax={req['pax']}, budget={req.get('budget')}",
        done=True,
    )

    await emit(stream, "fetch", "📦", f"Загружаю варианты: {', '.join(req['needs'])}")
    options = fetch_options(req)
    candidates = prefilter_options(req, options, preference_text=clean_text)
    await emit(
        stream,
        "fetch",
        "📦",
        (
            f"→ рейсов: {len(candidates.get('flights', []))}, "
            f"отелей: {len(candidates.get('hotels', []))}, "
            f"страховок: {len(candidates.get('insurance', []))}, "
            f"аптека: {len(candidates.get('pharmacy', []))}, "
            f"ресторанов: {len(candidates.get('restaurants', []))}"
        ),
        done=True,
    )

    await emit(stream, "select", "🤔", f"Подбираю оптимальный набор под бюджет {req.get('budget')} ₸...")
    selection = build_selection(req, candidates, preference_text=clean_text)
    await emit(stream, "select", "🤔", "Выбрала лучший набор по бюджету и составу поездки.", done=True)

    ok, hint = evaluate_plan(req, selection, candidates)

    if not ok:
        fallback_selection = fallback_select_options(req, candidates)
        fallback_ok, fallback_hint = evaluate_plan(req, fallback_selection, candidates)
        if fallback_ok:
            await emit(stream, "evaluate", "fallback", "Using mock_data fallback selection.", done=True)
            selection = fallback_selection
            ok, hint = True, ""
        else:
            hint = fallback_hint or hint

    if not ok:
        await emit(stream, "evaluate", "⚠️", hint)
        selection = fallback_select_options(req, candidates)
        ok, hint = evaluate_plan(req, selection, candidates)

    if not ok:
        await emit(stream, "evaluate", "⚠️", "Не удалось собрать план", done=True)
        return await send_error(stream, "Не удалось собрать план в рамках бюджета", hint)

    plan = assemble_plan(req, selection, candidates)

    # Enrich itinerary days with per-date weather forecasts (non-blocking)
    if plan.get("start_date") and plan.get("end_date"):
        try:
            sd = date.fromisoformat(plan["start_date"])
            ed = date.fromisoformat(plan["end_date"])
            dates_list = []
            d = sd
            while d <= ed:
                dates_list.append(d.isoformat())
                d += timedelta(days=1)
            weather_by_date = await get_weather_for_dates(req["to_city"], dates_list)
            for day in plan.get("itinerary", []):
                if day.get("date") and day["date"] in weather_by_date:
                    day["weather"] = weather_by_date[day["date"]]
        except Exception as exc:
            print(f"[WARN] weather for dates failed: {exc}")

    save_plan(plan)

    await emit(
        stream,
        "assemble",
        "🎯",
        f"Plan собран: {len(plan['items'])} позиций, итог {plan['total']} ₸, бонус {plan['bonus']} ₸",
        done=True,
    )

    if stream:
        try:
            await stream.send_json({"type": "plan_ready", "plan": plan})
        except Exception:
            pass

    return plan


def fallback_select_options(req: dict, options: dict) -> dict:
    candidates = prefilter_options(req, options, preference_text="дешевле")
    return build_selection(req, candidates, preference_text="дешевле")


def _cheapest_matching(items: list[dict], to_city: str | None, field: str, price_field: str) -> dict | None:
    matching = [
        item
        for item in items
        if _matches_destination(to_city, item.get(field))
    ]
    candidates = matching or items
    return min(candidates, key=lambda item: int(item.get(price_field, 0))) if candidates else None


def _best_rated_matching(items: list[dict], to_city: str | None, field: str) -> dict | None:
    matching = [
        item
        for item in items
        if _matches_destination(to_city, item.get(field))
    ]
    candidates = matching or items
    return max(candidates, key=lambda item: float(item.get("rating", 0))) if candidates else None


def _matches_destination(to_city: str | None, value: str | None) -> bool:
    if not to_city or not value:
        return True

    aliases = {
        "астана": {"астана", "astana", "nqz"},
        "алматы": {"алматы", "almaty", "ala"},
        "актобе": {"актобе", "ақтөбе", "aktobe", "akx"},
        "Р°СЃС‚Р°РЅР°": {"Р°СЃС‚Р°РЅР°", "astana", "nqz"},
        "astana": {"Р°СЃС‚Р°РЅР°", "astana", "nqz"},
        "nqz": {"Р°СЃС‚Р°РЅР°", "astana", "nqz"},
        "Р°Р»РјР°С‚С‹": {"Р°Р»РјР°С‚С‹", "almaty", "ala"},
        "almaty": {"Р°Р»РјР°С‚С‹", "almaty", "ala"},
        "ala": {"Р°Р»РјР°С‚С‹", "almaty", "ala"},
        "aktobe": {"актобе", "ақтөбе", "aktobe", "akx"},
        "akx": {"актобе", "ақтөбе", "aktobe", "akx"},
    }
    expected = str(to_city).strip().lower()
    actual = str(value).strip().lower()
    city_groups = [
        {"астана", "astana", "nqz", "Р°СЃС‚Р°РЅР°"},
        {"алматы", "almaty", "ala", "Р°Р»РјР°С‚С‹"},
        {"актобе", "ақтөбе", "aktobe", "akx"},
    ]
    if any(expected in group and actual in group for group in city_groups):
        return True
    return actual in aliases.get(expected, {expected})


def _matches_trip_pharmacy(trip_type: str | None, item: dict) -> bool:
    if trip_type != "family_weekend":
        return True

    item_trip_type = str(item.get("trip_type", "")).strip().lower()
    return item_trip_type in {"семейная", "family", "family_weekend", "СЃРµРјРµР№РЅР°СЏ".lower()}
