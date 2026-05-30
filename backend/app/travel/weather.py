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


def _fallback(city):
    return {"temp": None, "description": "Прогноз недоступен", "source": "fallback"}
