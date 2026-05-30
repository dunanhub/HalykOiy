from datetime import date, timedelta


def generate_itinerary(
    req: dict,
    items: list[dict],
    weather_by_date: dict | None = None,
) -> list[dict]:
    """
    Distributes plan items into a day-by-day schedule.
    Day 1: arrival (flight + transfer + hotel check-in).
    Last day: morning activities/restaurants, then checkout + return flight.
    Middle days: activities spread evenly, restaurants across evenings.
    """
    start_date_str = req.get("start_date")
    nights = int(req.get("nights") or 1)
    days_count = int(req.get("days") or (nights + 1))
    days_count = max(1, days_count)

    flights = [i for i in items if i["category"] == "flight"]
    hotels = [i for i in items if i["category"] == "hotel"]
    transfers = [i for i in items if i["category"] == "transfer"]
    restaurants = [i for i in items if i["category"] == "restaurant"]
    activities = [i for i in items if i["category"] == "activity"]

    # Build empty days
    itinerary: list[dict] = []
    for day_num in range(1, days_count + 1):
        day_date = None
        if start_date_str:
            try:
                sd = date.fromisoformat(start_date_str)
                day_date = (sd + timedelta(days=day_num - 1)).isoformat()
            except ValueError:
                pass

        weather = None
        if weather_by_date and day_date:
            weather = weather_by_date.get(day_date)

        itinerary.append({
            "day": day_num,
            "date": day_date,
            "title": "",
            "items": [],
            "weather": weather,
        })

    # --- Day 1: arrival ---
    d1 = itinerary[0]
    for f in flights:
        d1["items"].append({"type": "flight", "icon": "✈️", "title": f["title"], "details": f.get("details", "")})
    for t in transfers[:1]:
        d1["items"].append({"type": "transfer", "icon": "🚗", "title": t["title"]})
    for h in hotels:
        d1["items"].append({"type": "hotel", "icon": "🏨", "title": f"Заселение: {h['title']}"})
    d1["title"] = "День приезда"

    # --- Last day: departure items (collected separately, added AFTER activities/restaurants) ---
    departure_items: list[dict] = []
    if days_count > 1:
        for h in hotels:
            departure_items.append({"type": "hotel", "icon": "🏨", "title": f"Выселение: {h['title']}"})
        for t in transfers[1:2]:
            departure_items.append({"type": "transfer", "icon": "🚗", "title": t["title"]})
        from_city = req.get("from_city", "Алматы")
        departure_items.append({"type": "flight", "icon": "✈️", "title": f"Обратный рейс → {from_city}"})
        itinerary[-1]["title"] = "День отъезда"

    def _act_item(act: dict) -> dict:
        return {
            "type": "activity", "icon": "🎭",
            "title": act["title"], "details": act.get("details", ""),
        }

    def _rest_item(rest: dict) -> dict:
        return {
            "type": "restaurant", "icon": "🍽️",
            "title": rest["title"], "details": rest.get("details", ""),
        }

    # --- Distribute activities ---
    if days_count == 1:
        for act in activities:
            itinerary[0]["items"].append(_act_item(act))
    elif days_count == 2:
        # 2-day trip: split activities between Day 1 afternoon (after arrival)
        # and Day 2 morning (before departure)
        n = len(activities)
        day1_count = (n + 1) // 2  # first half goes to Day 1 (ceiling)
        for i, act in enumerate(activities):
            target_day = itinerary[0] if i < day1_count else itinerary[-1]
            target_day["items"].append(_act_item(act))
    else:
        # 3+ day trip: distribute across middle days
        middle = itinerary[1:-1]
        n_mid = len(middle)
        n_act = len(activities)
        if n_act >= n_mid:
            for i, act in enumerate(activities):
                middle[i % n_mid]["items"].append(_act_item(act))
        elif n_act > 0:
            step = max(1, n_mid // max(n_act, 1))
            for idx, act in enumerate(activities):
                day_idx = min(idx * step, n_mid - 1)
                middle[day_idx]["items"].append(_act_item(act))

    # --- Distribute restaurants ---
    # Day 1 evening (after check-in) gets first restaurant.
    # Subsequent restaurants spread across middle days.
    # Last day (departure) does NOT get a restaurant — no time before flight.
    if restaurants:
        if days_count == 1:
            for rest in restaurants:
                itinerary[0]["items"].append(_rest_item(rest))
        elif days_count == 2:
            # Only one realistic dinner — Day 1 evening
            itinerary[0]["items"].append(_rest_item(restaurants[0]))
        else:
            # Spread across days 1..(last-1)
            rest_days = itinerary[:-1]
            for r_idx, rest in enumerate(restaurants):
                target_idx = min(r_idx, len(rest_days) - 1)
                rest_days[target_idx]["items"].append(_rest_item(rest))

    # --- Attach departure items to last day AFTER activities and restaurants ---
    if days_count > 1 and departure_items:
        itinerary[-1]["items"].extend(departure_items)

    # --- Fill missing titles ---
    to_city = req.get("to_city", "городе")
    for day in itinerary:
        if not day["title"]:
            act_items = [i for i in day["items"] if i["type"] == "activity"]
            if act_items:
                day["title"] = act_items[0]["title"]
            elif day["items"]:
                day["title"] = f"День в {to_city}"
            else:
                day["title"] = "Свободный день"

    return itinerary
