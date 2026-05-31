from .itinerary_generator import generate_itinerary


INTENT_PATTERNS = {
    "add_activity": (
        "добавь активн", "добавить активн", "добавь развлечен",
        "добавь музей", "добавь кино", "ещё активн", "еще активн",
        "добавь ещё", "добавь еще",
    ),
    "add_restaurant": ("добавь ресторан", "добавить ресторан", "ещё ресторан", "еще ресторан"),
    "remove_pharmacy": ("убрать аптек", "убери аптек", "без аптек", "убрать набор", "убери набор"),
}


def detect_modification_intent(text: str) -> str | None:
    lower = (text or "").lower()
    for intent, patterns in INTENT_PATTERNS.items():
        if any(p in lower for p in patterns):
            return intent
    return None


def add_activity_to_plan(current_plan: dict, req: dict, candidates: dict) -> dict:
    """Adds one new activity to existing plan. Preserves all existing items."""
    existing_ids = {
        item["id"]
        for item in current_plan.get("items", [])
        if item.get("category") == "activity"
    }

    candidate = next(
        (a for a in candidates.get("activities", []) if str(a.get("id")) not in existing_ids),
        None,
    )
    if not candidate:
        return current_plan

    from .assembler import title_for, details_for
    from .evaluator import price_for

    new_item = {
        "category": "activity",
        "id": str(candidate["id"]),
        "title": title_for("activity", candidate),
        "details": details_for("activity", candidate, req),
        "price": price_for("activity", candidate, req),
        "optional": True,
    }

    updated_items = list(current_plan["items"]) + [new_item]
    total = sum(i.get("price", 0) for i in updated_items)

    updated = dict(current_plan)
    updated["items"] = updated_items
    updated["total"] = total
    updated["bonus"] = round(total * 0.02)
    updated["itinerary"] = generate_itinerary(req, updated_items)
    return updated


def add_restaurant_to_plan(current_plan: dict, req: dict, candidates: dict) -> dict:
    """Adds one new restaurant to existing plan."""
    existing_ids = {
        item["id"]
        for item in current_plan.get("items", [])
        if item.get("category") == "restaurant"
    }

    candidate = next(
        (r for r in candidates.get("restaurants", []) if str(r.get("id")) not in existing_ids),
        None,
    )
    if not candidate:
        return current_plan

    from .assembler import title_for, details_for
    from .evaluator import price_for

    new_item = {
        "category": "restaurant",
        "id": str(candidate["id"]),
        "title": title_for("restaurant", candidate),
        "details": details_for("restaurant", candidate, req),
        "price": price_for("restaurant", candidate, req),
    }

    updated_items = list(current_plan["items"]) + [new_item]
    total = sum(i.get("price", 0) for i in updated_items)

    updated = dict(current_plan)
    updated["items"] = updated_items
    updated["total"] = total
    updated["bonus"] = round(total * 0.02)
    updated["itinerary"] = generate_itinerary(req, updated_items)
    return updated


def remove_category_from_plan(current_plan: dict, category: str) -> dict:
    updated_items = [i for i in current_plan.get("items", []) if i.get("category") != category]
    total = sum(i.get("price", 0) for i in updated_items)
    updated = dict(current_plan)
    updated["items"] = updated_items
    updated["total"] = total
    updated["bonus"] = round(total * 0.02)
    return updated
