import uuid

from .checklist_generator import generate_checklist
from .constants import CATEGORY_ORDER
from .evaluator import find_item, price_for
from .utils import choice_ids, selection_body


def title_for(category: str, item: dict) -> str:
    if category == "flight":
        return f"{item.get('airline', 'Flight')} {item.get('from', '')}→{item.get('to', '')}"

    if category == "hotel":
        return item.get("title", "Hotel")

    if category == "insurance":
        return item.get("title", "Insurance")

    if category == "restaurant":
        return item.get("name", "Restaurant")

    if category == "activity":
        return item.get("title", "Активность")

    if category == "transfer":
        return f"{item.get('provider', 'Трансфер')} · {item.get('car_type', '')}"

    return item.get("title", str(item.get("id", category)))


def details_for(category: str, item: dict, req: dict) -> str:
    if category == "flight":
        return f"{item.get('departure')}–{item.get('arrival')} · {req['pax']} чел"

    if category == "hotel":
        family = "семейный" if item.get("family_friendly") else "стандартный"
        return f"{req['nights']} ночи · {family}"

    if category == "insurance":
        return str(item.get("provider", ""))

    if category == "pharmacy":
        return ", ".join(item.get("contents", [])) or "optional"

    if category == "restaurant":
        return f"{item.get('cuisine', '')} · ★{item.get('rating', '')}"

    if category == "activity":
        provider = f" · {item.get('provider')}" if item.get("provider") else ""
        return f"{item.get('duration', '')} · ★{item.get('rating', '')}{provider}"

    if category == "transfer":
        pax = int(req.get("pax", 1))
        nights = int(req.get("nights", 2))
        n_rides = 2 + nights * 2
        return f"≈{n_rides} поездок · аэропорт туда/обратно + {nights} дней · ETA {item.get('eta_minutes')} мин"

    return ""


def assemble_plan(req: dict, selection: dict, options: dict) -> dict:
    items = []
    selected = selection_body(selection)

    for category in CATEGORY_ORDER:
        choice = selected.get(category)
        if category == "pharmacy" and choice is None:
            choice = [
                {"id": item["id"]}
                for item in options.get("pharmacy", [])
                if item.get("id")
            ]

        if category == "activity" and choice is None:
            activities = [act for act in options.get("activities", []) if act.get("id")]
            if activities:
                choice = [{"id": activities[0]["id"]}]

        if category == "transfer" and choice is None:
            transfers = options.get("transfers", [])
            if transfers:
                choice = [{"id": transfers[0]["id"]}]

        for item_id in choice_ids(choice):
            item = find_item(category, item_id, options)
            if not item:
                continue

            items.append(
                {
                    "category": "travel_kit" if category == "pharmacy" else category,
                    "id": str(item.get("id")),
                    "title": title_for(category, item),
                    "details": details_for(category, item, req),
                    "price": price_for(category, item, req),
                    **(
                        {
                            "disclaimer": item.get("disclaimer"),
                            "optional": True,
                        }
                        if category in {"pharmacy", "activity", "transfer"}
                        else {}
                    ),
                }
            )

    items = dedupe_items(items)
    total = sum(item["price"] for item in items)
    budget = req.get("budget")
    within_budget = True if budget is None else total <= budget

    return {
        "plan_id": str(uuid.uuid4()),
        "trip": {
            "from": req["from_city"],
            "to": req["to_city"],
            "dates": req["dates"],
            "pax": req["pax"],
            "nights": req["nights"],
            "type": req["trip_type"],
        },
        "family_members": req.get("family_members"),
        "items": items,
        "total": total,
        "budget": budget,
        "within_budget": within_budget,
        "can_book": within_budget,
        "bonus": round(total * 0.02),
        "checklist": _build_checklist(req),
    }


def _build_checklist(req: dict) -> list[dict]:
    members = req.get("family_members")
    if members:
        return generate_checklist(members)
    pax = int(req.get("pax") or 1)
    generic = [{"role": "взрослый", "age": None, "name": None} for _ in range(pax)]
    return generate_checklist(generic)


def dedupe_items(items: list) -> list:
    seen = set()
    result = []
    for item in items:
        key = (item.get("category"), item.get("id"))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
