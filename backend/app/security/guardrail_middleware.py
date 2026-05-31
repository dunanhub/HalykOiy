"""
Guardrail FastAPI Middleware для Halyk Travel Companion.

Перехватывает все запросы к защищённым эндпоинтам,
прогоняет через GuardrailChecker и блокирует вредоносный ввод.
"""

import json
import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .guardrails import GuardrailChecker, GuardrailVerdict
from .config import config

logger = logging.getLogger("security.guardrail_middleware")


class GuardrailMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware для проверки входящих запросов.

    Применяется к путям из config.PROTECTED_PATHS.
    Извлекает текст из JSON body (поле 'message' или 'query')
    и прогоняет через GuardrailChecker.

    Использование в main.py:
        from app.security import GuardrailMiddleware, get_guardrail_checker

        checker = get_guardrail_checker(redis_client)
        app.add_middleware(GuardrailMiddleware, checker=checker)
    """

    def __init__(self, app, checker: GuardrailChecker):
        super().__init__(app)
        self.checker = checker

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Пропускаем незащищённые пути
        if not self._is_protected(request.url.path):
            return await call_next(request)

        # Пропускаем GET/OPTIONS/HEAD
        if request.method in ("GET", "OPTIONS", "HEAD"):
            return await call_next(request)

        # Извлекаем текст из body
        user_text = await self._extract_text(request)
        if user_text is None:
            return await call_next(request)

        # Извлекаем session_id из headers или cookies
        session_id = (
            request.headers.get("X-Session-ID")
            or request.cookies.get("session_id")
            or request.client.host
            or "anonymous"
        )

        # Проверяем через guardrail
        result = await self.checker.check(user_text, session_id=session_id)

        if result.verdict in (
            GuardrailVerdict.BLOCKED,
            GuardrailVerdict.BLOCKED_LLM,
        ):
            logger.warning(
                f"Request blocked: path={request.url.path}, "
                f"verdict={result.verdict}, reason={result.reason}, "
                f"session={session_id}"
            )
            return JSONResponse(
                status_code=422,
                content={
                    "error": "guardrail_blocked",
                    "message": result.reason,
                    "verdict": result.verdict.value,
                },
            )

        if result.verdict == GuardrailVerdict.RATE_LIMITED:
            logger.warning(
                f"Rate limited: session={session_id}"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limited",
                    "message": result.reason,
                    "retry_after": 60,
                },
            )

        # Логируем подозрительные, но пропускаем
        if result.verdict == GuardrailVerdict.SUSPICIOUS:
            logger.info(
                f"Suspicious input passed: score={result.score}, "
                f"session={session_id}"
            )

        return await call_next(request)

    def _is_protected(self, path: str) -> bool:
        """Проверяет, является ли путь защищённым."""
        return any(path.startswith(p) for p in config.PROTECTED_PATHS)

    async def _extract_text(self, request: Request) -> str | None:
        """
        Извлекает текст пользователя из JSON body.
        Ищет поля: message, query, text, prompt.
        """
        try:
            body = await request.body()
            if not body:
                return None

            data = json.loads(body)

            # Поддерживаем несколько форматов запроса
            for field in ("message", "query", "text", "prompt"):
                if field in data and isinstance(data[field], str):
                    return data[field]

            return None

        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
