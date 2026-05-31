"""
Halyk Travel AI — Backend.
С интегрированным слоем безопасности (Бекзат КБ).
"""

import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket

# ─── Роутеры ──────────────────────────────────────────────────
from app.routers.flights import router as flights_router
from app.routers.hotels import router as hotels_router
from app.routers.transfer import router as transfer_router
from app.routers.activities import router as activities_router
from app.routers.pharmacy import router as pharmacy_router
from app.routers.pay import router as pay_router
from app.routers.restaurants import router as restaurants_router
from app.routers.insurance import router as insurance_router
from app.routers.travel import router as travel_router
from workflow import run_workflow

# ─── Security (Бекзат КБ) ────────────────────────────────────
from app.security import (
    PIITokenizer,
    GuardrailChecker,
    GuardrailMiddleware,
    AuditMiddleware,
    CredentialBroker,
    audit_logger,
    AuditAction,
    config,
)
from app.security.hardening import setup_security
from app.security.env_checker import run_security_checks
from app.security.session import SessionManager

logger = logging.getLogger("halyk_travel")

# ─── Глобальные security-инстансы ─────────────────────────────
redis_client: aioredis.Redis = None
tokenizer: PIITokenizer = None
guardrail_checker: GuardrailChecker = GuardrailChecker(redis_client=None)
cred_broker: CredentialBroker = None
session_mgr: SessionManager = None


# ─── Lifespan ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app):
    global redis_client, tokenizer, guardrail_checker, cred_broker, session_mgr

    # 1. Security checks при старте
    run_security_checks(".")

    # 2. Redis
    redis_client = aioredis.from_url(config.REDIS_URL, decode_responses=True)
    logger.info(f"✅ Redis connected: {config.REDIS_URL}")

    # 3. Security компоненты
    tokenizer = PIITokenizer(redis_client)
    guardrail_checker = GuardrailChecker(redis_client)
    cred_broker = CredentialBroker(redis_client)
    session_mgr = SessionManager(redis_client)
    logger.info("✅ Security layer initialized")

    yield

    # Shutdown
    await redis_client.close()
    logger.info("Redis disconnected")


# ─── App ──────────────────────────────────────────────────────

app = FastAPI(title="Halyk Travel AI", lifespan=lifespan)

# ─── Security Middleware (порядок важен!) ─────────────────────
# Последний добавленный = первый в цепочке запроса.
# Поток: Request → SecurityHeaders → Guardrail → Audit → Router

app.add_middleware(AuditMiddleware)
app.add_middleware(GuardrailMiddleware, checker=guardrail_checker)

# Security headers + strict CORS (заменяет allow_origins=["*"])
setup_security(app, cors_origins=[
    "http://localhost:3000",       # Nuxt dev
    "http://127.0.0.1:3000",
    "http://100.79.161.43:3000",
    "http://192.168.10.3:3000",
    "http://halyk_frontend:3000",  # Docker internal
])

# ─── Роутеры ──────────────────────────────────────────────────

app.include_router(flights_router)
app.include_router(hotels_router)
app.include_router(transfer_router)
app.include_router(activities_router)
app.include_router(pharmacy_router)
app.include_router(pay_router)
app.include_router(restaurants_router)
app.include_router(insurance_router)
app.include_router(travel_router)


@app.get("/")
async def root():
    return {"status": "ok", "security": "enabled"}


# ─── WebSocket с guardrail ────────────────────────────────────

@app.websocket("/ws/travel")
async def travel_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        user_text = data.get("text", "")

        if not user_text.strip():
            await websocket.send_json({"type": "error", "text": "Укажи куда хочешь поехать"})
            return

        # ─── GUARDRAIL: проверяем вход ────────────────────────
        if guardrail_checker:
            gr_result = guardrail_checker._rule_based_check(user_text)
            if gr_result.verdict.value != "pass":
                audit_logger.log_guardrail(
                    session_id="ws",
                    action=user_text[:100],
                    blocked=True,
                    reason=gr_result.reason,
                )
                await websocket.send_json({
                    "type": "error",
                    "text": "Запрос заблокирован системой безопасности.",
                })
                return

        # ─── PII TOKENIZE: маскируем ПДн перед LLM ───────────
        clean_text = user_text
        pii_session = None
        if tokenizer:
            try:
                clean_text, pii_session = await tokenizer.tokenize(user_text, session_id="ws")
            except Exception:
                clean_text = user_text  # fallback — не ломаем flow

        # ─── Audit log ────────────────────────────────────────
        audit_logger.log_user_message(
            session_id="ws",
            message=clean_text[:200],
            ip=websocket.client.host if websocket.client else "unknown",
        )

        # ─── Основной workflow ────────────────────────────────
        await run_workflow(
            clean_text,
            stream=websocket,
            partial_request=data.get("partial_request"),
            current_plan=data.get("current_plan"),
        )

    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "text": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
