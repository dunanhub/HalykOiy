from typing import Literal

from pydantic import BaseModel, Field


class TravelRequest(BaseModel):
    text: str = Field(..., min_length=2)
    partial_request: dict | None = None


class ConfirmPaymentRequest(BaseModel):
    plan_id: str = Field(..., min_length=8)


class TripRequest(BaseModel):
    from_city: str = "Алматы"
    to_city: str
    dates: str = "выходные"
    nights: int = 2
    pax: int = 2
    budget: int | None = None
    trip_type: Literal["family_weekend", "business", "leisure", "medical"] = "family_weekend"
    needs: list[str]


class ThinkingMessage(BaseModel):
    type: str = "thinking"
    step: str
    icon: str
    text: str
    status: Literal["in_progress", "done"] = "in_progress"
