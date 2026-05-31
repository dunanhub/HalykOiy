"""
API Hardening Middleware для Halyk Travel.

Добавляет security headers и strict CORS на каждый ответ.
Закрывает: XSS, clickjacking, MIME sniffing, MITM, CORS bypass.
"""

import logging
from typing import List, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("security.hardening")


# ─── Security Headers ─────────────────────────────────────────

SECURITY_HEADERS = {
    # Защита от MIME-sniffing (IE/Edge отрабатывают скрипт из image/png)
    "X-Content-Type-Options": "nosniff",

    # Защита от clickjacking — наш API нельзя фреймить
    "X-Frame-Options": "DENY",

    # XSS-фильтр браузера (legacy, но не вредит)
    "X-XSS-Protection": "1; mode=block",

    # HSTS — браузер запомнит что мы HTTPS-only (1 год)
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",

    # CSP — запрещаем загрузку ресурсов с чужих доменов
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",

    # Не раскрываем технологии
    "X-Powered-By": "",

    # Referrer — не отправляем полный URL на чужие сайты
    "Referrer-Policy": "strict-origin-when-cross-origin",

    # Permissions Policy — отключаем опасные API браузера
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(self)",

    # Кэш — не кэшировать ответы с PII
    "Cache-Control": "no-store, no-cache, must-revalidate, private",
    "Pragma": "no-cache",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware: добавляет security headers на каждый HTTP-ответ.

    Использование:
        app.add_middleware(SecurityHeadersMiddleware)
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # Добавляем все security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        # Удаляем Server header (не раскрывать uvicorn/starlette version)
        if "server" in response.headers:
            del response.headers["server"]

        return response


# ─── CORS Configuration ────────────────────────────────────────

# Разрешённые источники (фронтенд)
DEFAULT_ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",       # Nuxt dev server
    "http://localhost:5173",       # Vite dev server (fallback)
    "http://127.0.0.1:3000",
]

# Для продакшна добавить:
# "https://halyktravel.kz",
# "https://www.halyktravel.kz",


def setup_cors(
    app: FastAPI,
    allowed_origins: Optional[List[str]] = None,
    allow_credentials: bool = True,
) -> None:
    """
    Настраивает strict CORS на FastAPI-приложении.

    Args:
        app: FastAPI приложение.
        allowed_origins: Список разрешённых origin. По умолчанию — localhost.
        allow_credentials: Разрешить cookies/auth headers.
    """
    origins = allowed_origins or DEFAULT_ALLOWED_ORIGINS

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,           # НЕ ["*"] — только наши фронтенды
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST"],   # Только нужные методы
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Session-ID",
            "X-Request-ID",
        ],
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Remaining",
        ],
        max_age=600,                     # Preflight кэш 10 мин
    )

    logger.info(f"CORS configured: origins={origins}")


# ─── Удобная функция для main.py ──────────────────────────────

def setup_security(app: FastAPI, cors_origins: Optional[List[str]] = None):
    """
    Одна строка для подключения всей защиты в main.py:

        from app.security.hardening import setup_security
        setup_security(app)

    Подключает:
    1. Security headers (X-Frame-Options, HSTS, CSP, ...)
    2. Strict CORS (только localhost:3000 по умолчанию)
    """
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS
    setup_cors(app, cors_origins)

    logger.info("✅ Security hardening applied")
