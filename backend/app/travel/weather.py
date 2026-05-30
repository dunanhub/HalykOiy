from datetime import date

import httpx


CITY_COORDS = {
    "астана": (51.16, 71.47),
    "алматы": (43.24, 76.89),
    "шымкент": (42.32, 69.59),
    "актобе": (50.28, 57.17),
    "ақтөбе": (50.28, 57.17),
}

WEATHER_CODES = {
    0: "Ясно",
    1: "Преимущественно ясно",
    2: "Переменная облачность",
    3: "Облачно",
    45: "Туман",
    61: "Дождь",
    71: "Снег",
    80: "Ливни",
}

# Open-Meteo supports up to 16 days of daily forecast
_FORECAST_HORIZON_DAYS = 16


async def get_weather(city: str) -> dict:
    coords = CITY_COORDS.get((city or "").lower())
    if not coords:
        return _fallback(city)

    lat, lon = coords
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code"
    )
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
            data = response.json()
            current = data["current"]
            return {
                "temp": round(current["temperature_2m"]),
                "description": WEATHER_CODES.get(current["weather_code"], "—"),
                "source": "open-meteo",
            }
    except Exception as exc:
        print(f"[WARN] weather fallback: {exc}")
        return _fallback(city)


async def get_weather_for_dates(city: str, dates: list[str]) -> dict[str, dict]:
    """Returns {date_str: {temp, description, source}} for each date."""
    if not dates:
        return {}

    coords = CITY_COORDS.get((city or "").lower())
    if not coords:
        return {d: _date_fallback() for d in dates}

    today = date.today()
    cutoff = (today.toordinal() + _FORECAST_HORIZON_DAYS)

    # Separate dates within and beyond forecast range
    in_range = [d for d in dates if _date_in_range(d, today, cutoff)]
    out_of_range = [d for d in dates if not _date_in_range(d, today, cutoff)]

    result: dict[str, dict] = {}

    # Dates beyond forecast horizon get a fallback immediately
    for d in out_of_range:
        result[d] = {
            "temp": None,
            "description": "Прогноз будет доступен ближе к дате",
            "source": "fallback",
        }

    if not in_range:
        return result

    lat, lon = coords
    start_date = min(in_range)
    end_date = max(in_range)

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,weather_code"
        f"&start_date={start_date}&end_date={end_date}"
        f"&timezone=auto"
    )

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            data = response.json()
            daily = data.get("daily", {})
            day_dates = daily.get("time", [])
            temps = daily.get("temperature_2m_max", [])
            codes = daily.get("weather_code", [])

            api_map: dict[str, dict] = {}
            for i, day_date in enumerate(day_dates):
                temp = temps[i] if i < len(temps) else None
                code = codes[i] if i < len(codes) else None
                api_map[day_date] = {
                    "temp": round(temp) if temp is not None else None,
                    "description": WEATHER_CODES.get(int(code), "—") if code is not None else "—",
                    "source": "open-meteo",
                }

            for d in in_range:
                result[d] = api_map.get(d, _date_fallback())

    except Exception as exc:
        print(f"[WARN] get_weather_for_dates fallback: {exc}")
        for d in in_range:
            result[d] = _date_fallback()

    return result


def _date_in_range(date_str: str, today: date, cutoff_ordinal: int) -> bool:
    try:
        d = date.fromisoformat(date_str)
        return today.toordinal() <= d.toordinal() <= cutoff_ordinal
    except ValueError:
        return False


def _date_fallback() -> dict:
    return {"temp": None, "description": "Прогноз недоступен", "source": "fallback"}


def _fallback(city):
    return {"temp": None, "description": "Прогноз недоступен", "source": "fallback"}
