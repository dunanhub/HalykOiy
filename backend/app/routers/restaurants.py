from fastapi import APIRouter
from app.services.data_loader import load_json

router = APIRouter(
    prefix="/api/restaurants",
    tags=["Restaurants"]
)

@router.get("/")
async def get_restaurants(city: str):
    restaurants = load_json("restaurants.json")

    return [
        item
        for item in restaurants
        if item["city"].lower() == city.lower()
    ]