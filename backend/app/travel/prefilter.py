CITY_MAP = {
    "астана": "astana",
    "нур-султан": "astana",
    "алматы": "almaty",
    "актобе": "aktobe",
    "astana": "astana",
    "nqz": "astana",
    "almaty": "almaty",
    "ala": "almaty",
    "aktobe": "aktobe",
    "akx": "aktobe",
    "рђсѓс‚р°рѕр°": "astana",
    "рђсљрјр°с‚с‹": "almaty",
}

AIRPORT_MAP = {
    "алматы": "ALA",
    "астана": "NQZ",
    "актобе": "AKX",
    "нур-султан": "NQZ",
    "almaty": "ALA",
    "astana": "NQZ",
    "aktobe": "AKX",
    "ala": "ALA",
    "nqz": "NQZ",
    "akx": "AKX",
    "рђсљрјр°с‚с‹": "ALA",
    "рђсѓс‚р°рѕр°": "NQZ",
}

CITY_ALIASES = {
    "astana": {"astana", "nqz", "астана", "нур-султан", "рђсѓс‚р°рѕр°", "рђсѓс‚р°рЅр°"},
    "almaty": {"almaty", "ala", "алматы", "рђсљрјр°с‚с‹", "рђр»рјр°с‚с‹"},
    "aktobe": {"aktobe", "akx", "актобе", "ақтөбе"},
}

def _flight_score(flight: dict, trip_type: str, budget_per_pax: int = 0) -> float:
    price = int(flight.get("price_per_person", 999999))
    departure = str(flight.get("departure", "23:59"))
    morning_bonus = -3000 if trip_type == "family_weekend" and departure < "12:00" else 0
    if budget_per_pax >= 150_000:
        # High budget: prefer premium (higher price) flights
        return -(price + morning_bonus)
    return price + morning_bonus


def _hotel_score(hotel: dict, budget: int = 0) -> float:
    rating = float(hotel.get("rating", 0))
    price = int(hotel.get("price_per_night", 999999))
    if budget >= 300_000:
        # Very high budget: pure rating + small price bonus to favor premium
        return -(rating * 10000 + price / 100)
    if budget >= 150_000:
        # Moderate-high budget: rating-weighted, minimal price penalty
        return -(rating * 4000 - price / 400)
    return -(rating * 1000 - price / 10)


def _insurance_score(insurance: dict) -> float:
    coverage = float(insurance.get("coverage", 0))
    price = float(insurance.get("price", 1) or 1)
    return -(coverage / price)


def _city_matches(expected_city: str, actual_city: str | None) -> bool:
    expected = _norm(expected_city)
    actual = _norm(actual_city)

    if not expected:
        return True
    if expected in actual:
        return True

    aliases = CITY_ALIASES.get(CITY_MAP.get(expected, expected), {expected})
    return actual in aliases


def _norm(value) -> str:
    return str(value or "").strip().lower()


def prefilter_options(req: dict, options: dict, preference_text: str = "") -> dict:
    result = {}
    preference_text = _norm(preference_text)
    to_city_ru = _norm(req.get("to_city"))
    from_city_ru = _norm(req.get("from_city") or "алматы")
    city_en = CITY_MAP.get(to_city_ru, to_city_ru)
    from_code = AIRPORT_MAP.get(from_city_ru, "ALA")
    to_code = AIRPORT_MAP.get(to_city_ru, "NQZ")
    trip_type = req.get("trip_type", "leisure")
    budget = int(req.get("budget") or 0)
    pax = int(req.get("pax") or 1)
    budget_per_pax = budget // max(pax, 1)

    flights = [
        flight
        for flight in options.get("flights", [])
        if _norm(flight.get("from")) == from_code.lower()
        and _norm(flight.get("to")) == to_code.lower()
    ]
    if not flights:
        flights = [
            flight
            for flight in options.get("flights", [])
            if _norm(flight.get("to")) == to_code.lower()
        ]
    if not flights:
        flights = list(options.get("flights", []))
    flights.sort(key=lambda flight: _flight_score(flight, trip_type, budget_per_pax))
    result["flights"] = flights[:5]

    hotels = [
        hotel
        for hotel in options.get("hotels", [])
        if _city_matches(city_en, hotel.get("city"))
    ]
    if trip_type == "family_weekend":
        family_hotels = [hotel for hotel in hotels if hotel.get("family_friendly")]
        hotels = family_hotels or hotels
    hotels.sort(
        key=lambda hotel: (_preference_boost(preference_text, hotel, ("title", "city")), -_hotel_score(hotel, budget)),
        reverse=True,
    )
    result["hotels"] = hotels[:5]

    result["insurance"] = sorted(options.get("insurance", []), key=_insurance_score)[:3]

    restaurants = [
        restaurant
        for restaurant in options.get("restaurants", [])
        if _city_matches(city_en, restaurant.get("city"))
    ]
    restaurants.sort(
        key=lambda restaurant: (
            _preference_boost(preference_text, restaurant, ("name", "cuisine")),
            float(restaurant.get("rating", 0)),
            -int(restaurant.get("avg_check", 0)),
        ),
        reverse=True,
    )
    result["restaurants"] = restaurants[:5]

    pharmacy = options.get("pharmacy", [])
    has_kids = bool(req.get("family_members")) and any(
        _norm(member.get("role")) in {"ребёнок", "ребенок", "child", "kid", "сђрµр±с’рѕрѕрє"}
        for member in (req.get("family_members") or [])
        if isinstance(member, dict)
    )
    kit_id = "kit_2" if has_kids else "kit_1"
    kit = next((item for item in pharmacy if item.get("id") == kit_id), None)
    result["pharmacy"] = [kit] if kit else []

    # Activities: filter by city and audience
    pax = int(req.get("pax") or 1)
    has_kids = bool(req.get("family_members")) and any(
        _norm(member.get("role")) in {"ребёнок", "ребенок", "child", "kid"}
        for member in (req.get("family_members") or [])
        if isinstance(member, dict)
    )
    trip_type = req.get("trip_type", "leisure")

    if has_kids or trip_type == "family_weekend":
        target_audiences = {"семья с детьми", "группа", "культурный"}
    elif pax == 1:
        target_audiences = {"соло", "культурный", "активный отдых"}
    elif pax == 2:
        target_audiences = {"пара", "культурный", "активный отдых"}
    else:
        target_audiences = {"группа", "культурный", "активный отдых"}

    activities = [
        a for a in options.get("activities", [])
        if _city_matches(city_en, a.get("city"))
        and (a.get("audience") in target_audiences or a.get("audience") == "все")
    ]
    activities.sort(
        key=lambda activity: (
            _preference_boost(preference_text, activity, ("title", "audience")),
            float(activity.get("rating", 0)),
            -int(activity.get("price", 0)),
        ),
        reverse=True,
    )
    from .date_utils import activity_target_count
    target = activity_target_count(req)
    result["activities"] = activities[:max(target + 3, 6)]

    # Transfer: prefer InDrive and Halyk Taxi
    all_transfers = options.get("transfers", [])
    preferred_providers = ["inDrive Partner", "Halyk Taxi Partner", "Yandex Go Partner"]
    if pax > 4:
        preferred_car_types = ["минивэн", "комфорт+", "комфорт"]
    else:
        preferred_car_types = ["эконом", "комфорт", "комфорт+"]

    def _transfer_score(t: dict) -> tuple:
        type_idx = preferred_car_types.index(t.get("car_type", "")) if t.get("car_type") in preferred_car_types else 99
        prov_idx = preferred_providers.index(t.get("provider", "")) if t.get("provider") in preferred_providers else 99
        return (type_idx, prov_idx, int(t.get("base_price", 9999)))

    sorted_transfers = sorted(all_transfers, key=_transfer_score)
    result["transfers"] = sorted_transfers[:3]

    return result


def _preference_boost(text: str, item: dict, fields: tuple[str, ...]) -> int:
    if not text:
        return 0

    haystack = " ".join(str(item.get(field, "")) for field in fields).lower()
    score = 0
    for token in ("кино", "каяк", "музей", "спа", "премиум", "люкс", "итальян", "мексикан", "семейн"):
        if token in text and token in haystack:
            score += 5
    if "kino.kz" in haystack and "кино" in text:
        score += 10
    return score
