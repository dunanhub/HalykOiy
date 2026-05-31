from fastapi import APIRouter, WebSocket

from .plan_store import get_plan
from .runner import run_workflow
from .schemas import ConfirmPaymentRequest, TravelRequest


router = APIRouter()


@router.post("/api/travel/plan")
async def create_plan(payload: TravelRequest):
    return await run_workflow(payload.text, partial_request=payload.partial_request)


@router.post("/api/confirm-payment")
async def confirm_payment(payload: ConfirmPaymentRequest):
    plan = get_plan(payload.plan_id)
    if not plan:
        return {
            "status": "error",
            "text": "План устарел или не найден",
            "can_book": False,
        }

    if not plan.get("can_book"):
        return {
            "status": "error",
            "text": "План нельзя оплатить: нужно увеличить бюджет или изменить услуги",
            "plan_id": payload.plan_id,
            "can_book": False,
        }

    return {
        "status": "paid_mock",
        "plan_id": payload.plan_id,
        "amount": plan["total"],
        "bonus": plan["bonus"],
        "next_trip": plan.get("next_trip"),
        "message": "Оплата Halyk Pay эмулирована. Реального списания нет.",
    }


@router.websocket("/ws/travel-plan")
async def travel_plan_ws(websocket: WebSocket):
    await websocket.accept()

    try:
        data = await websocket.receive_json()
        message = data.get("text") or data.get("message")

        if not message:
            await websocket.send_json({"type": "error", "text": "Пустой запрос"})
            return

        await run_workflow(message, stream=websocket, partial_request=data.get("partial_request"))

    except Exception as exc:
        await websocket.send_json({"type": "error", "text": f"Ошибка WebSocket: {exc}"})
