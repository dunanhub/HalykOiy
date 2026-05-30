from fastapi import APIRouter
from app.services.data_loader import load_json

router = APIRouter(prefix="/api/flights", tags=["Flights"])

@router.get("/")
async def get_flights(from_: str = "ALA", to: str = "NQZ", date: str = "...", pax: int = 4):
    flights = load_json("flights.json")

    result = []

    for flight in flights:
        if flight["from"] == from_ and flight["to"] == to:
            result.append({
                **flight,
                "date": date,
                "total_price": flight["price_per_person"] * pax
            })

    return result