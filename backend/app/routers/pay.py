from fastapi import APIRouter
from pydantic import BaseModel
from uuid import uuid4
from app.services.data_loader import load_json

router = APIRouter(prefix="/api/pay", tags=["Payment"])

class PayRequest(BaseModel):
    plan_id: str
    total: int
    items: list

@router.post("/")
async def pay(data: PayRequest):
    payment_settings = load_json("pay.json")

    bonus = int(data.total * payment_settings["bonus_rate"])

    return {
        "success": True,
        "provider": payment_settings["provider"],
        "transaction_id": str(uuid4()),
        "plan_id": data.plan_id,
        "currency": payment_settings["currency"],
        "total": data.total,
        "bonus": bonus,
        "message": "Payment confirmed by user action"
    }