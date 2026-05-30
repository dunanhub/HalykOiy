from fastapi import APIRouter
from pydantic import BaseModel
from app.services.data_loader import load_json

router = APIRouter(prefix="/api/transfer", tags=["Transfer"])

class TransferRequest(BaseModel):
    from_location: str
    to_location: str
    pax: int
    luggage: bool = True

@router.post("/")
async def calculate_transfer(data: TransferRequest):
    transfers = load_json("transfer.json")

    result = []

    for transfer in transfers:
        total_price = (
            transfer["base_price"]
            + data.pax * transfer["price_per_pax"]
            + (transfer["luggage_price"] if data.luggage else 0)
        )

        result.append({
            **transfer,
            "from": data.from_location,
            "to": data.to_location,
            "pax": data.pax,
            "luggage": data.luggage,
            "price": total_price
        })

    return result