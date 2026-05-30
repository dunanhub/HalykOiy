from datetime import date, timedelta


def get_today() -> date:
    return date.today()


def next_weekend_dates() -> tuple[date, date]:
    """Returns nearest Saturday and Sunday."""
    today = date.today()
    weekday = today.weekday()  # Mon=0, Sat=5, Sun=6
    days_until_sat = (5 - weekday) % 7
    if days_until_sat == 0:
        days_until_sat = 7
    sat = today + timedelta(days=days_until_sat)
    return sat, sat + timedelta(days=1)


def normalize_trip_dates(req: dict) -> dict:
    """
    Fills start_date / end_date / nights / days from text or explicit fields.
    Does NOT invent start_date for long trips without explicit date.
    Returns updated dict.
    """
    req = dict(req)
    today = date.today()
    dates_text = str(req.get("dates") or "").lower().strip()
    start_date = req.get("start_date")
    end_date = req.get("end_date")
    nights = req.get("nights")
    days = req.get("days")

    if ("выходн" in dates_text) and not start_date:
        sat, sun = next_weekend_dates()
        start_date = sat.isoformat()
        end_date = sun.isoformat()
        nights = 1
        days = 2
    elif "завтра" in dates_text and not start_date:
        tomorrow = today + timedelta(days=1)
        start_date = tomorrow.isoformat()
    elif ("через неделю" in dates_text or "следующие выходные" in dates_text) and not start_date:
        sat, _ = next_weekend_dates()
        start_date = (sat + timedelta(days=7)).isoformat()

    if start_date and not end_date:
        try:
            sd = date.fromisoformat(start_date)
            if nights is not None:
                end_date = (sd + timedelta(days=int(nights))).isoformat()
                days = int(nights) + 1
            elif days is not None:
                end_date = (sd + timedelta(days=int(days) - 1)).isoformat()
                nights = max(0, int(days) - 1)
        except (ValueError, TypeError):
            pass

    if nights is not None and days is None:
        try:
            days = int(nights) + 1
        except (TypeError, ValueError):
            pass
    elif days is not None and nights is None:
        try:
            nights = max(0, int(days) - 1)
        except (TypeError, ValueError):
            pass

    req["start_date"] = start_date
    req["end_date"] = end_date
    if nights is not None:
        req["nights"] = int(nights)
    if days is not None:
        req["days"] = int(days)

    return req


def needs_start_date_clarification(req: dict) -> bool:
    """Returns True if trip is long (>3 nights) and start_date is unknown."""
    if req.get("start_date"):
        return False
    dates_text = str(req.get("dates") or "").lower()
    if "выходн" in dates_text or "завтра" in dates_text:
        return False
    nights = req.get("nights")
    days = req.get("days")
    if nights is not None:
        try:
            return int(nights) > 3
        except (TypeError, ValueError):
            pass
    if days is not None:
        try:
            return int(days) > 4
        except (TypeError, ValueError):
            pass
    return False


def activity_target_count(req: dict) -> int:
    """Roughly ~1 activity per available day, capped to a realistic max."""
    days = req.get("days")
    if days is None:
        nights = req.get("nights")
        days = int(nights or 1) + 1
    days = int(days)

    if days <= 2:
        base = 1
    elif days <= 4:
        base = days - 1     # 2-3
    elif days <= 7:
        base = days - 2     # 3-5
    elif days <= 14:
        base = days // 2 + 1   # 5-8
    else:
        base = min(days // 2, 10)

    try:
        budget = int(req.get("budget") or 0)
        pax = int(req.get("pax") or 1)
        per_person = budget // max(pax, 1)
        if days <= 2 and per_person >= 150_000:
            base = 2   # weekend with budget: one Day 1 afternoon + one Day 2 morning
        elif days <= 7 and per_person >= 200_000:
            base = min(base + 1, days)
    except (TypeError, ValueError):
        pass

    return max(1, base)
