import uuid

from .checklist_generator import generate_checklist
from .constants import CATEGORY_ORDER
from .date_utils import activity_target_count
from .evaluator import find_item, price_for
from .itinerary_generator import generate_itinerary
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

        if category == "activity":
            activities = [act for act in options.get("activities", []) if act.get("id")]
            target = activity_target_count(req)
            if activities and target:
                # Selector's pick goes first, then fill up to target with top candidates
                already_picked = set()
                if choice:
                    for aid in choice_ids(choice):
                        already_picked.add(str(aid))

                ordered_ids: list[str] = [str(aid) for aid in already_picked]
                for act in activities:
                    if len(ordered_ids) >= target:
                        break
                    aid = str(act["id"])
                    if aid not in already_picked:
                        ordered_ids.append(aid)
                        already_picked.add(aid)
                choice = [{"id": aid} for aid in ordered_ids]

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
    budget = req.get("budget")
    if budget:
        items = _trim_to_budget(items, int(budget))
    total = sum(item["price"] for item in items)
    within_budget = True if budget is None else total <= budget

    itinerary = generate_itinerary(req, items)

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
        "start_date": req.get("start_date"),
        "end_date": req.get("end_date"),
        "days": req.get("days"),
        "itinerary": itinerary,
    }


def _build_checklist(req: dict) -> list[dict]:
    members = req.get("family_members")
    if members:
        return generate_checklist(members)
    pax = int(req.get("pax") or 1)
    if pax == 1:
        return generate_checklist([{"role": "взрослый", "age": None, "name": "Я"}])
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


def _trim_to_budget(items: list, budget: int) -> list:
    """
    Remove optional items in priority order until total is within budget.
    Order: extra activities (keep ≥1) → pharmacy → transfer.
    Never removes required items (flight/hotel/insurance/restaurant) or the
    last remaining activity.
    """
    total = sum(int(item.get("price", 0)) for item in items)
    if total <= budget:
        return items

    items = list(items)
    while total > budget:
        activities = [i for i in items if i.get("category") == "activity"]
        if len(activities) > 1:
            victim = max(activities, key=lambda x: int(x.get("price", 0)))
            items.remove(victim)
            total -= int(victim.get("price", 0))
            continue

        pharmacy = [i for i in items if i.get("category") == "travel_kit"]
        if pharmacy:
            victim = pharmacy[0]
            items.remove(victim)
            total -= int(victim.get("price", 0))
            continue

        transfer = [i for i in items if i.get("category") == "transfer"]
        if transfer:
            victim = transfer[0]
            items.remove(victim)
            total -= int(victim.get("price", 0))
            continue

        break
    return items
