from fastapi import APIRouter
from app.services.data_loader import load_json

router = APIRouter(prefix="/api/activities", tags=["Activities"])

@router.get("/")
async def get_activities(city: str, audience: str = "family_kids"):
    activities = load_json("activities.json")

    return [
        item
        for item in activities
        if item["city"].lower() == city.lower()
        and item["audience"] == audience
    ]