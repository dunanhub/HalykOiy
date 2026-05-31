from .constants import NEED_TO_OPTIONS_KEY
from .utils import choice_ids, first_choice_id, selection_body


OPTIONAL_NEEDS = {"pharmacy", "activity", "transfer"}


def find_item(category: str, item_id: str, options: dict) -> dict | None:
    key = NEED_TO_OPTIONS_KEY.get(category)
    if not key:
        return None

    for item in options.get(key, []):
        if str(item.get("id")) == str(item_id):
            return item

    return None


def price_for(category: str, item: dict, req: dict) -> int:
    if category == "flight":
        return int(item.get("price_per_person", 0)) * int(req["pax"])

    if category == "hotel":
        return int(item.get("price_per_night", 0)) * int(req["nights"])

    if category == "insurance":
        return int(item.get("price", 0)) * int(req.get("pax", 1))

    if category == "restaurant":
        return int(item.get("avg_check", item.get("price", 0))) * int(req.get("pax", 1))

    if category == "activity":
        return int(item.get("price", 0)) * int(req.get("pax", 1))

    if category == "transfer":
        pax = int(req.get("pax", 1))
        nights = int(req.get("nights", 2))
        n_rides = 2 + nights * 2
        price_per_ride = int(item.get("base_price", 0)) + int(item.get("price_per_pax", 0)) * pax
        return price_per_ride * n_rides

    return int(item.get("price", 0))


def compute_total(selection: dict, options: dict, req: dict) -> int:
    total = 0
    selected = _with_required_pharmacy(selection_body(selection), options)

    for category, choice in selected.items():
        for item_id in choice_ids(choice):
            item = find_item(category, item_id, options)
            if item:
                total += price_for(category, item, req)

    return total


def evaluate_plan(req: dict, selection: dict, options: dict) -> tuple[bool, str]:
    selected = _with_required_pharmacy(selection_body(selection), options)
    total = compute_total({"selection": selected}, options, req)
    budget = req.get("budget")

    if total <= 0:
        return False, "План пустой или сумма равна 0."

    for category, choice in selected.items():
        for item_id in choice_ids(choice):
            if not find_item(category, item_id, options):
                return False, f"Выбранный id {item_id} не найден в категории {category}."

    flight_id = first_choice_id(selected.get("flight"))
    if flight_id:
        flight = find_item("flight", flight_id, options)
        if flight and not _matches_destination(req.get("to_city"), flight.get("to")):
            return False, "Рейс не совпадает с городом назначения."

    hotel_id = first_choice_id(selected.get("hotel"))
    if hotel_id:
        hotel = find_item("hotel", hotel_id, options)
        if hotel and not _matches_destination(req.get("to_city"), hotel.get("city")):
            return False, "Отель не совпадает с городом назначения."

    required_pharmacy = {
        str(item["id"])
        for item in options.get("pharmacy", [])
        if item.get("required") is True
        and item.get("id")
        and _matches_trip_pharmacy(req.get("trip_type"), item)
    }
    chosen_pharmacy = set(choice_ids(selected.get("pharmacy")))

    if required_pharmacy and not required_pharmacy.issubset(chosen_pharmacy):
        return False, "Не все обязательные позиции аптечки выбраны."

    if budget is not None and total > budget:
        return False, f"Превышен бюджет на {total - budget} ₸. Выбери более дешёвый набор."

    for need in req.get("needs", []):
        if need in OPTIONAL_NEEDS:
            continue
        key = NEED_TO_OPTIONS_KEY.get(need)
        if key and options.get(key) and need not in selected:
            return False, f"Не выбрана категория {need}. Добавь её в selection."

    return True, ""


def _matches_destination(to_city: str | None, value: str | None) -> bool:
    if not to_city or not value:
        return True

    aliases = {
        "астана": {"астана", "astana", "nqz"},
        "алматы": {"алматы", "almaty", "ala"},
        "астана": {"астана", "astana", "nqz"},
        "astana": {"астана", "astana", "nqz"},
        "nqz": {"астана", "astana", "nqz"},
        "алматы": {"алматы", "almaty", "ala"},
        "almaty": {"алматы", "almaty", "ala"},
        "ala": {"алматы", "almaty", "ala"},
        "актобе": {"актобе", "ақтөбе", "aktobe", "akx"},
        "ақтөбе": {"актобе", "ақтөбе", "aktobe", "akx"},
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


def _with_required_pharmacy(selected: dict, options: dict) -> dict:
    result = dict(selected)
    if "pharmacy" not in result and options.get("pharmacy"):
        result["pharmacy"] = [
            {"id": item["id"]}
            for item in options["pharmacy"]
            if item.get("id")
        ]
    return result


def _matches_trip_pharmacy(trip_type: str | None, item: dict) -> bool:
    if trip_type != "family_weekend":
        return True

    item_trip_type = str(item.get("trip_type", "")).strip().lower()
    return item_trip_type in {"семейная", "family", "family_weekend", "СЃРµРјРµР№РЅР°СЏ".lower()}
