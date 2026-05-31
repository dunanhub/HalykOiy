"""
Audit Logger для Halyk Travel Companion.

Записывает все действия системы в аудит-лог.
ПДн автоматически маскируются перед записью.

Формат: JSON Lines (каждая строка — отдельное событие).
"""

import json
import time
import logging
import os
from typing import Optional, Any, Dict
from enum import Enum
from pathlib import Path

from .tokenizer import mask_pii_for_logs
from .config import config

logger = logging.getLogger("security.audit")


class AuditAction(str, Enum):
    """Типы действий для аудит-лога."""
    USER_MESSAGE = "user_message"          # Сообщение пользователя
    LLM_CALL = "llm_call"                 # Вызов LLM
    LLM_RESPONSE = "llm_response"         # Ответ LLM
    TOOL_CALL = "tool_call"               # Вызов партнёрского инструмента
    TOOL_RESPONSE = "tool_response"        # Ответ инструмента
    PAYMENT_ATTEMPT = "payment_attempt"    # Попытка оплаты
    PAYMENT_CONFIRMED = "payment_confirmed"  # Оплата подтверждена
    PAYMENT_REJECTED = "payment_rejected"  # Оплата отклонена
    GUARDRAIL_BLOCK = "guardrail_block"    # Заблокировано guardrail
    GUARDRAIL_PASS = "guardrail_pass"      # Пропущено guardrail
    PII_TOKENIZED = "pii_tokenized"        # ПДн токенизированы
    SESSION_START = "session_start"        # Начало сессии
    SESSION_END = "session_end"            # Конец сессии
    ERROR = "error"                        # Ошибка


class AuditLogger:
    """
    Аудит-логгер с автоматической маскировкой ПДн.

    Использование:
        audit = AuditLogger()

        # Логируем действие
        audit.log(
            action=AuditAction.USER_MESSAGE,
            session_id="abc123",
            details={"message": "Я Иванов Иван, ИИН 010203456789"},
            ip="192.168.1.1",
        )
        # В логе: {"message": "Я [NAME_MASKED], ИИН [IIN_MASKED]"}
    """

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or config.AUDIT_LOG_FILE
        self.mask_pii = config.AUDIT_MASK_PII

        # Создаём директорию для логов
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        action: AuditAction,
        session_id: str = "anonymous",
        details: Optional[Dict[str, Any]] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Записывает событие в аудит-лог.

        Args:
            action: Тип действия.
            session_id: ID сессии.
            details: Дополнительные данные (ПДн будут замаскированы).
            ip: IP-адрес клиента.
            user_agent: User-Agent заголовок.
        """
        # Маскируем ПДн в деталях
        masked_details = self._mask_details(details) if details else None

        entry = {
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "action": action.value,
            "session_id": session_id,
            "details": masked_details,
            "ip": ip,
            "user_agent": user_agent,
        }

        # Записываем в файл
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except IOError as e:
            logger.error(f"Failed to write audit log: {e}")

        # Дублируем в Python logger
        logger.info(
            f"AUDIT [{action.value}] session={session_id} "
            f"ip={ip or 'unknown'}"
        )

    def _mask_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Рекурсивно маскирует ПДн в деталях."""
        if not self.mask_pii:
            return details

        masked = {}
        for key, value in details.items():
            if isinstance(value, str):
                masked[key] = mask_pii_for_logs(value)
            elif isinstance(value, dict):
                masked[key] = self._mask_details(value)
            elif isinstance(value, list):
                masked[key] = [
                    mask_pii_for_logs(v) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                masked[key] = value

        return masked

    def log_user_message(self, session_id: str, message: str, ip: str = None):
        """Shortcut: логируем сообщение пользователя."""
        self.log(
            action=AuditAction.USER_MESSAGE,
            session_id=session_id,
            details={"message": message},
            ip=ip,
        )

    def log_llm_call(
        self,
        session_id: str,
        model: str,
        prompt_preview: str,
    ):
        """Shortcut: логируем вызов LLM."""
        self.log(
            action=AuditAction.LLM_CALL,
            session_id=session_id,
            details={
                "model": model,
                "prompt_preview": prompt_preview[:200],  # Ограничиваем длину
            },
        )

    def log_tool_call(
        self,
        session_id: str,
        tool_name: str,
        args: Dict[str, Any],
    ):
        """Shortcut: логируем вызов инструмента."""
        self.log(
            action=AuditAction.TOOL_CALL,
            session_id=session_id,
            details={
                "tool": tool_name,
                "args": args,
            },
        )

    def log_payment(
        self,
        session_id: str,
        action: AuditAction,
        amount: float,
        currency: str = "KZT",
        payment_id: Optional[str] = None,
    ):
        """Shortcut: логируем платёжное действие."""
        self.log(
            action=action,
            session_id=session_id,
            details={
                "amount": amount,
                "currency": currency,
                "payment_id": payment_id or "unknown",
            },
        )

    def log_guardrail(
        self,
        session_id: str,
        verdict: str,
        score: float,
        reason: str,
        ip: str = None,
    ):
        """Shortcut: логируем результат guardrail."""
        action = (
            AuditAction.GUARDRAIL_BLOCK
            if verdict != "pass"
            else AuditAction.GUARDRAIL_PASS
        )
        self.log(
            action=action,
            session_id=session_id,
            details={
                "verdict": verdict,
                "score": score,
                "reason": reason,
            },
            ip=ip,
        )


# Singleton
audit_logger = AuditLogger()
