from fastapi import APIRouter
from app.services.data_loader import load_json

router = APIRouter(
    prefix="/api/insurance",
    tags=["Insurance"]
)

@router.get("/")
async def get_insurance():
    return load_json("insurance.json")