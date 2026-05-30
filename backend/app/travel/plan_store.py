import time


PLAN_TTL_SECONDS = 3600
_PLANS: dict[str, tuple[float, dict]] = {}


def save_plan(plan: dict) -> None:
    _PLANS[plan["plan_id"]] = (time.time() + PLAN_TTL_SECONDS, plan)


def get_plan(plan_id: str) -> dict | None:
    record = _PLANS.get(plan_id)
    if not record:
        return None

    expires_at, plan = record
    if expires_at < time.time():
        _PLANS.pop(plan_id, None)
        return None

    return plan
