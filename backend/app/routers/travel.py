from copy import deepcopy
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.data_loader import load_json

router = APIRouter(prefix="/api/travel", tags=["Travel"])

BONUS_RATE = 0.02
DEFAULT_BUDGET = 150_000
DEFAULT_PAX = 4


class PlanRequest(BaseModel):
    message: str


class EditRequest(BaseModel):
    plan: dict
    message: str


def _money(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " ₸"


def _recalculate(plan: dict) -> dict:
    total = sum(item["price"] for item in plan["items"])
    budget = plan.get("budget", DEFAULT_BUDGET)

    plan["total"] = total
    plan["budget"] = budget
    plan["within_budget"] = total <= budget
    plan["bonus"] = int(total * BONUS_RATE)

    return plan


def _build_plan() -> dict:
    flights = load_json("flights.json")
    hotels = load_json("hotels.json")
    insurance = load_json("insurance.json")
    pharmacy = load_json("pharmacy.json")
    restaurants = load_json("restaurants.json")

    flight = min(
        (item for item in flights if item["from"] == "ALA" and item["to"] == "NQZ"),
        key=lambda item: item["price_per_person"],
    )
    hotel = min(
        (item for item in hotels if item["city"].lower() == "astana" and item["family_friendly"]),
        key=lambda item: item["price_per_night"],
    )
    insurance_item = next(
        item for item in insurance if item["provider"] == "Halyk Insurance"
    )
    pharmacy_items = [item for item in pharmacy if item["trip_type"] == "family" and item["required"]]
    restaurant = next(item for item in restaurants if item["name"] == "Navat")

    plan = {
        "plan_id": str(uuid4()),
        "trip": {
            "from": "Алматы",
            "to": "Астана",
            "dates": "Суббота-воскресенье",
            "nights": 2,
            "pax": DEFAULT_PAX,
            "type": "family_weekend",
        },
        "items": [
            {
                "category": "flight",
                "title": flight["airline"],
                "details": (
                    f"Алматы → Астана · {flight['departure']}-{flight['arrival']} "
                    f"· {DEFAULT_PAX} билета"
                ),
                "price": flight["price_per_person"] * DEFAULT_PAX,
            },
            {
                "category": "hotel",
                "title": hotel["title"],
                "details": f"2 ночи · семейный номер · ★ {hotel['rating']}",
                "price": hotel["price_per_night"] * 2,
            },
            {
                "category": "insurance",
                "title": insurance_item["provider"],
                "details": f"{insurance_item['title']} · семья {DEFAULT_PAX} человека",
                "price": insurance_item["price"],
            },
            {
                "category": "pharmacy",
                "title": "Аптечка в дорогу",
                "details": " + ".join(item["title"] for item in pharmacy_items),
                "price": sum(item["price"] for item in pharmacy_items),
            },
            {
                "category": "restaurant",
                "title": restaurant["name"],
                "details": f"{restaurant['cuisine']} кухня · семейный ресторан · ★ {restaurant['rating']}",
                "price": restaurant["avg_check"],
            },
        ],
    }

    return _recalculate(plan)


@router.get("/thinking")
async def get_thinking_steps():
    plan = _build_plan()

    return [
        {
            "step": "extract",
            "icon": "🔍",
            "text": "Анализирую запрос: семья · Астана · выходные · бюджет 150 000 ₸",
            "status": "done",
        },
        {
            "step": "flights",
            "icon": "✈️",
            "text": "Ищу билеты Алматы → Астана: найден FlyArystan за 88 000 ₸",
            "status": "done",
        },
        {
            "step": "hotel",
            "icon": "🏨",
            "text": "Подбираю семейный отель: Nomad Family Hotel на 2 ночи",
            "status": "done",
        },
        {
            "step": "insurance",
            "icon": "🛡️",
            "text": "Добавляю Halyk Insurance для всей семьи",
            "status": "done",
        },
        {
            "step": "pharmacy",
            "icon": "💊",
            "text": "Собираю аптечку в дорогу: жаропонижающее и антисептик",
            "status": "done",
        },
        {
            "step": "restaurant",
            "icon": "🍽️",
            "text": "Добавляю ресторан Navat для семейного ужина",
            "status": "done",
        },
        {
            "step": "budget",
            "icon": "💰",
            "text": f"Считаю итог: {_money(plan['total'])} из {_money(plan['budget'])}, бонусов +{_money(plan['bonus'])}",
            "status": "done",
        },
    ]


@router.post("/plan")
async def create_plan(data: PlanRequest):
    _ = data.message

    return _build_plan()


@router.post("/edit")
async def edit_plan(data: EditRequest):
    plan = deepcopy(data.plan)
    message = data.message.lower()

    if "ресторан" in message or "restaurant" in message or "navat" in message:
        plan["items"] = [
            item for item in plan["items"] if item.get("category") != "restaurant"
        ]

    plan["plan_id"] = str(uuid4())

    return _recalculate(plan)
