from .date_utils import needs_start_date_clarification


def get_missing_fields(req: dict) -> list:
    missing = []
    if not req.get("to_city"):
        missing.append("to_city")
    if not req.get("pax"):
        missing.append("pax")
    pax = req.get("pax") or 0
    if req.get("trip_type") == "family_weekend" and pax >= 3 and not req.get("family_members"):
        missing.append("family_members")
    if needs_start_date_clarification(req):
        missing.append("start_date")
    if req.get("budget") is None:
        missing.append("budget")
    return missing


def build_clarification(req: dict) -> dict | None:
    missing = get_missing_fields(req)
    if not missing:
        return None

    if "to_city" in missing:
        return _q(req, missing, "Куда хотите поехать?", ["Астана", "Алматы", "Актобе", "Шымкент"])

    if "pax" in missing or "family_members" in missing:
        return _q(
            req,
            missing,
            "Кто едет с вами?",
            ["Один", "Вдвоём", "Семья: 2 взрослых + 2 ребёнка", "Другое"],
        )

    if "start_date" in missing:
        return _q(req, missing, "На какую дату планируете поездку?", [
            "На ближайшие выходные",
            "Завтра",
            "Через неделю",
            "Выбрать дату",
        ])

    if "budget" in missing:
        return _q(
            req,
            missing,
            "Какой примерный бюджет поездки?",
            ["До 100 000 ₸", "До 150 000 ₸", "До 250 000 ₸", "Без лимита"],
        )

    return None


def _q(req, missing, question, quick_replies):
    return {
        "status": "need_clarification",
        "question": question,
        "quick_replies": quick_replies,
        "missing_fields": missing,
        "partial_request": req,
    }


def merge_requests(old: dict, new: dict) -> dict:
    merged = dict(old or {})
    for key, value in (new or {}).items():
        if value is not None:
            merged[key] = value
    return merged


def apply_quick_reply(text: str, req: dict) -> dict:
    normalized = (text or "").strip().lower()
    if not normalized:
        return req

    if normalized == "один":
        req["pax"] = 1
        req["family_members"] = None
        req["trip_type"] = "leisure"
    elif normalized == "вдвоём" or normalized == "вдвоем":
        req["pax"] = 2
        req["family_members"] = None
        req["trip_type"] = "leisure"
    elif ("2 взрослых" in normalized and "2 ребён" in normalized) or (
        "2 взрослых" in normalized and "2 ребен" in normalized
    ):
        req["pax"] = 4
        req["trip_type"] = "family_weekend"
        req["family_members"] = [
            {"role": "взрослый", "age": None, "name": None},
            {"role": "взрослый", "age": None, "name": None},
            {"role": "ребёнок", "age": None, "name": None},
            {"role": "ребёнок", "age": None, "name": None},
        ]

    if "100" in normalized:
        req["budget"] = 100000
    elif "150" in normalized:
        req["budget"] = 150000
    elif "250" in normalized:
        req["budget"] = 250000
    elif "без лимита" in normalized:
        req["budget"] = 999999999

    city_replies = {
        "астана": "Астана",
        "алматы": "Алматы",
        "шымкент": "Шымкент",
        "актобе": "Актобе",
    }
    if normalized in city_replies:
        req["to_city"] = city_replies[normalized]

    return req
