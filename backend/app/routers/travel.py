from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.travel.editor import update_plan
from app.travel.plan_store import save_plan
from app.travel.runner import run_workflow
from app.travel.weather import get_weather


router = APIRouter(prefix="/api/travel", tags=["Travel"])


class PlanRequest(BaseModel):
    text: str = Field(..., min_length=2)
    partial_request: dict | None = None


class EditRequest(BaseModel):
    plan: dict
    message: str = Field(..., min_length=2)


@router.get("/thinking")
async def get_thinking_steps():
    return [
        {
            "step": "extract",
            "icon": "🔍",
            "text": "Разбираю город, бюджет, состав поездки и пожелания.",
            "status": "done",
        },
        {
            "step": "fetch",
            "icon": "📦",
            "text": "Собираю релевантные кандидаты из mock_data.",
            "status": "done",
        },
        {
            "step": "select",
            "icon": "🤔",
            "text": "Считаю лучший набор по бюджету, а не генерирую его с нуля.",
            "status": "done",
        },
    ]


@router.get("/weather")
async def travel_weather(city: str):
    return await get_weather(city)


@router.post("/plan")
async def create_plan(data: PlanRequest):
    return await run_workflow(data.text, partial_request=data.partial_request)


@router.post("/edit")
async def edit_plan(data: EditRequest):
    plan = update_plan(data.plan, data.message)
    save_plan(plan)
    return plan
