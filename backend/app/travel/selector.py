from itertools import product

from .evaluator import price_for
from .utils import choice_ids


OPTIONAL_CATEGORIES = {"pharmacy", "activity", "transfer"}


def build_selection(req: dict, options: dict, preference_text: str = "") -> dict:
    preference_text = (preference_text or "").lower()
    budget = req.get("budget")

    required_categories = [
        category
        for category in ("flight", "hotel", "insurance", "restaurant")
        if category in req.get("needs", []) and options.get(_options_key(category))
    ]
    optional_categories = [
        category
        for category in ("transfer", "pharmacy", "activity")
        if category in req.get("needs", []) and options.get(_options_key(category))
    ]

    category_choices = {category: _build_choice_list(category, options) for category in required_categories}
    for category in optional_categories:
        category_choices[category] = [None] + _build_choice_list(category, options)

    if not required_categories:
        return {"selection": {}}

    best_selection = None
    best_score = None

    ordered_categories = required_categories + optional_categories
    ordered_choices = [category_choices[category] for category in ordered_categories]

    for combo in product(*ordered_choices):
        selection = {}
        total = 0
        valid = True

        for category, choice in zip(ordered_categories, combo):
            if choice is None:
                continue

            selection[category] = choice
            for item_id in choice_ids(choice):
                item = _find_by_id(options.get(_options_key(category), []), item_id)
                if not item:
                    valid = False
                    break
                total += price_for(category, item, req)
            if not valid:
                break

        if not valid:
            continue

        total_score = _selection_score(selection, req, options, preference_text, total, budget)
        if best_score is None or total_score > best_score:
            best_score = total_score
            best_selection = selection

    return {"selection": best_selection or {}}


def _build_choice_list(category: str, options: dict) -> list:
    items = options.get(_options_key(category), [])
    if category == "pharmacy":
        return [[{"id": str(item["id"])}] for item in items if item.get("id")]
    return [{"id": str(item["id"]), "reason": "python selector"} for item in items if item.get("id")]


def _selection_score(selection: dict, req: dict, options: dict, preference_text: str, total: int, budget: int | None) -> float:
    if budget is not None and total > budget:
        return -1_000_000 - (total - budget)

    score = 0.0
    score += _budget_fit_score(total, budget, preference_text)

    for category, choice in selection.items():
        for item_id in choice_ids(choice):
            item = _find_by_id(options.get(_options_key(category), []), item_id)
            if item:
                score += _item_score(category, item, req, preference_text)

    return score


def _budget_fit_score(total: int, budget: int | None, preference_text: str) -> float:
    if budget is None:
        return 0

    remaining = budget - total
    if remaining < 0:
        return -remaining * 5

    if _wants_cheaper(preference_text):
        return -(total / 800)

    utilization = total / budget if budget > 0 else 1.0

    if _wants_premium(preference_text):
        return -(remaining / 120)

    if utilization < 0.20:
        return -(remaining / 200)
    if utilization < 0.50:
        return -(remaining / 400)
    if utilization < 0.85:
        return -(remaining / 800)
    return -(remaining / 1500)


def _item_score(category: str, item: dict, req: dict, preference_text: str) -> float:
    pax = int(req.get("pax") or 1)

    if category == "flight":
        score = 120 - int(item.get("price_per_person", 0)) / 1200
        if req.get("trip_type") == "family_weekend" and str(item.get("departure", "23:59")) < "12:00":
            score += 18
        return score

    if category == "hotel":
        score = float(item.get("rating", 0)) * 30 - int(item.get("price_per_night", 0)) / 2500
        if req.get("trip_type") == "family_weekend" and item.get("family_friendly"):
            score += 15
        if _wants_premium(preference_text):
            score += int(item.get("price_per_night", 0)) / 5000
        return score

    if category == "insurance":
        coverage = float(item.get("coverage", 0))
        total_price = int(item.get("price", 0)) * pax
        return coverage / max(total_price, 1)

    if category == "restaurant":
        total_price = int(item.get("avg_check", 0)) * pax
        score = float(item.get("rating", 0)) * 25 - total_price / 3500
        if _match_keywords(preference_text, item, ("cuisine", "name")):
            score += 20
        if _wants_premium(preference_text):
            score += total_price / 8000
        return score

    if category == "activity":
        total_price = int(item.get("price", 0)) * pax
        score = float(item.get("rating", 0)) * 20 - total_price / 2500
        if _match_keywords(preference_text, item, ("title", "audience")):
            score += 40
        return score

    if category == "transfer":
        score = 30 - int(item.get("base_price", 0)) / 1200
        if item.get("car_type") == "комфорт+":
            score += 5
        if _match_keywords(preference_text, item, ("provider", "car_type")):
            score += 15
        return score

    if category == "pharmacy":
        if "апт" in preference_text or "дет" in preference_text:
            return 10
        return 2

    return 0


def _find_by_id(items: list[dict], item_id: str) -> dict | None:
    for item in items:
        if str(item.get("id")) == str(item_id):
            return item
    return None


def _options_key(category: str) -> str:
    return {
        "flight": "flights",
        "hotel": "hotels",
        "insurance": "insurance",
        "restaurant": "restaurants",
        "activity": "activities",
        "transfer": "transfers",
        "pharmacy": "pharmacy",
    }[category]


def _wants_premium(text: str) -> bool:
    return any(token in text for token in ("дорог", "премиум", "лучший", "комфорт", "люкс"))


def _wants_cheaper(text: str) -> bool:
    return any(token in text for token in ("дешев", "бюджет", "эконом", "подешев"))


def _match_keywords(text: str, item: dict, fields: tuple[str, ...]) -> bool:
    if not text:
        return False

    synonyms = {
        "кино": ("кино", "cinema", "кинотеатр"),
        "музей": ("музей",),
        "каяк": ("каяк", "каякинг"),
        "ресторан": ("ресторан",),
        "итальян": ("итальян",),
        "мяс": ("мяс", "steak", "barbecue"),
        "такси": ("такси", "yandex", "indrive", "bolt"),
    }
    haystack = " ".join(str(item.get(field, "")) for field in fields).lower()
    for token, variants in synonyms.items():
        if token in text and any(variant in haystack for variant in variants):
            return True
    return False
