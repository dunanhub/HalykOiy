import re

from .assembler import details_for, title_for
from .clarifier import apply_quick_reply
from .constants import CATEGORY_ORDER, DEFAULTS, NEED_TO_OPTIONS_KEY
from .evaluator import price_for
from .mock_repo import fetch_options
from .prefilter import prefilter_options
from .selector import _item_score, _wants_cheaper, build_selection
from .assembler import assemble_plan


REMOVE_WORDS = ("убрать", "убери", "удалить", "удали", "исключить", "исключи", "без")

CATEGORY_TOKENS = {
    "activity": ("актив", "кино", "каяк", "экскурс", "музей"),
    "restaurant": ("ресторан", "ужин", "кафе"),
    "hotel": ("отел", "гостиниц"),
    "flight": ("рейс", "билет", "перел"),
    "transfer": ("трансфер", "такси"),
    "travel_kit": ("аптек", "набор"),
}


def update_plan(existing_plan: dict, message: str) -> dict:
    req = _request_from_plan(existing_plan)
    message = (message or "").strip()
    lower = message.lower()

    req = apply_quick_reply(message, req)
    _apply_budget_override(req, lower)
    _apply_city_override(req, lower)

    options = fetch_options(req)
    candidates = prefilter_options(req, options, preference_text=lower)

    target = _target_category(lower)

    # Case 1: removal ("убрать ресторан")
    if _is_category_removal(lower) and target:
        display_cat = "travel_kit" if target == "travel_kit" else target
        updated_items = [
            item for item in existing_plan.get("items", [])
            if item.get("category") != display_cat
        ]
        return _rebuild_totals(existing_plan, updated_items)

    # Case 2: swap specific category ("поменяй ресторан на дешевле")
    if target:
        return _swap_category(existing_plan, target, req, candidates, lower)

    # Case 3: vague edit — full rebuild
    selection = build_selection(req, candidates, preference_text=lower)
    plan = assemble_plan(req, selection, candidates)
    plan["plan_id"] = existing_plan.get("plan_id", plan["plan_id"])
    return plan


def _swap_category(existing_plan: dict, category: str, req: dict, candidates: dict, preference_text: str) -> dict:
    options_key = NEED_TO_OPTIONS_KEY.get(category) or NEED_TO_OPTIONS_KEY.get(
        "pharmacy" if category == "travel_kit" else category
    )
    available = candidates.get(options_key, [])
    if not available:
        return existing_plan

    display_cat = "travel_kit" if category == "pharmacy" else category

    # Exclude items already in the plan so we pick something different
    existing_ids = {
        item["id"]
        for item in existing_plan.get("items", [])
        if item.get("category") == display_cat
    }
    alternatives = [item for item in available if str(item.get("id")) not in existing_ids]
    pool = alternatives if alternatives else available

    best = _pick_best(category, pool, req, preference_text)
    if not best:
        return existing_plan

    new_item = {
        "category": display_cat,
        "id": str(best.get("id")),
        "title": title_for(category, best),
        "details": details_for(category, best, req),
        "price": price_for(category, best, req),
    }
    if category in {"pharmacy", "activity", "transfer"}:
        new_item["optional"] = True
        if best.get("disclaimer"):
            new_item["disclaimer"] = best["disclaimer"]

    # Replace old items of this category, keep the rest
    other_items = [item for item in existing_plan.get("items", []) if item.get("category") != display_cat]
    all_items = other_items + [new_item]

    # Restore category order
    order_map = {cat: i for i, cat in enumerate(
        ["flight", "hotel", "insurance", "transfer", "travel_kit", "activity", "restaurant"]
    )}
    all_items.sort(key=lambda x: order_map.get(x.get("category", ""), 99))

    return _rebuild_totals(existing_plan, all_items)


def _pick_best(category: str, items: list[dict], req: dict, preference_text: str) -> dict | None:
    if not items:
        return None

    price_field = {
        "restaurant": "avg_check",
        "hotel": "price_per_night",
        "flight": "price_per_person",
        "activity": "price",
        "transfer": "base_price",
    }.get(category)

    def score(item):
        base = _item_score(category, item, req, preference_text)
        if _wants_cheaper(preference_text) and price_field:
            base -= int(item.get(price_field, 0)) / 400
        return base

    return max(items, key=score)


def _rebuild_totals(existing_plan: dict, items: list[dict]) -> dict:
    total = sum(int(item.get("price", 0)) for item in items)
    updated = dict(existing_plan)
    updated["items"] = items
    updated["total"] = total
    updated["bonus"] = round(total * 0.02)
    budget = int(updated.get("budget") or 0)
    updated["within_budget"] = budget == 0 or total <= budget
    updated["can_book"] = updated["within_budget"]
    return updated


def _request_from_plan(plan: dict) -> dict:
    trip = plan.get("trip", {})
    items = plan.get("items", [])
    needs = []
    for item in items:
        category = item.get("category")
        if category == "travel_kit":
            category = "pharmacy"
        if category and category not in needs:
            needs.append(category)

    merged_needs = list(DEFAULTS["needs"])
    for need in needs:
        if need not in merged_needs:
            merged_needs.append(need)

    return {
        "from_city": trip.get("from", DEFAULTS["from_city"]),
        "to_city": trip.get("to"),
        "dates": trip.get("dates", "выходные"),
        "nights": trip.get("nights", DEFAULTS["nights"]),
        "pax": trip.get("pax"),
        "budget": plan.get("budget"),
        "trip_type": trip.get("type", DEFAULTS["trip_type"]),
        "family_members": plan.get("family_members"),
        "needs": merged_needs,
    }


def _apply_budget_override(req: dict, lower: str) -> None:
    match = re.search(r"(\d+)\s*к", lower)
    if match:
        req["budget"] = int(match.group(1)) * 1000
        return
    match = re.search(r"(\d{5,7})", lower)
    if match:
        req["budget"] = int(match.group(1))


def _apply_city_override(req: dict, lower: str) -> None:
    for city in ("астана", "алматы", "актобе", "шымкент"):
        if city in lower:
            req["to_city"] = city.capitalize()
            return


def _is_category_removal(lower: str) -> bool:
    return any(word in lower for word in REMOVE_WORDS)


def _target_category(lower: str) -> str | None:
    for category, tokens in CATEGORY_TOKENS.items():
        if any(token in lower for token in tokens):
            return category
    return None
