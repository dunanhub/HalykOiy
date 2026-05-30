from fastapi import APIRouter
from app.services.data_loader import load_json

router = APIRouter(prefix="/api/hotels", tags=["Hotels"])

@router.get("/")
async def get_hotels(city: str, checkin: str, nights: int = 2, family: bool = True):
    hotels = load_json("hotels.json")

    result = []

    for hotel in hotels:
        if hotel["city"].lower() == city.lower():
            if family and not hotel["family_friendly"]:
                continue

            result.append({
                **hotel,
                "checkin": checkin,
                "nights": nights,
                "total_price": hotel["price_per_night"] * nights
            })

    return result