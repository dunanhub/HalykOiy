"""
Audit FastAPI Middleware для Halyk Travel Companion.

Автоматически логирует все входящие запросы и ответы.
ПДн маскируются перед записью.
"""

import time
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .audit import audit_logger, AuditAction

logger = logging.getLogger("security.audit_middleware")


class AuditMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware для аудит-логирования.

    Логирует:
    - Все входящие запросы (путь, метод, IP)
    - Время обработки (latency)
    - HTTP-статус ответа

    Использование в main.py:
        from app.security import AuditMiddleware

        app.add_middleware(AuditMiddleware)
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        start_time = time.time()

        # Извлекаем данные запроса
        session_id = (
            request.headers.get("X-Session-ID")
            or request.cookies.get("session_id")
            or "anonymous"
        )
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        path = request.url.path
        method = request.method

        # Пропускаем health check и статику
        if path in ("/health", "/favicon.ico", "/robots.txt"):
            return await call_next(request)

        # Обрабатываем запрос
        try:
            response = await call_next(request)
            latency_ms = (time.time() - start_time) * 1000

            # Логируем
            audit_logger.log(
                action=AuditAction.USER_MESSAGE,
                session_id=session_id,
                details={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "latency_ms": round(latency_ms, 2),
                },
                ip=client_ip,
                user_agent=user_agent,
            )

            # Предупреждаем о медленных запросах
            if latency_ms > 5000:
                logger.warning(
                    f"Slow request: {method} {path} "
                    f"took {latency_ms:.0f}ms, session={session_id}"
                )

            return response

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            audit_logger.log(
                action=AuditAction.ERROR,
                session_id=session_id,
                details={
                    "method": method,
                    "path": path,
                    "error": str(e),
                    "latency_ms": round(latency_ms, 2),
                },
                ip=client_ip,
                user_agent=user_agent,
            )
            raise
