from fastapi import APIRouter
from app.services.data_loader import load_json

router = APIRouter(prefix="/api/pharmacy", tags=["Pharmacy"])

@router.get("/travel-kit")
async def get_travel_kit(trip_type: str = "family"):
    pharmacy = load_json("pharmacy.json")

    return [
        item
        for item in pharmacy
        if item["trip_type"] == trip_type
    ]