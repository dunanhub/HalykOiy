"""
Конфигурация слоя безопасности Halyk Travel Companion.
Загружает настройки из переменных окружения с разумными дефолтами.
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class SecurityConfig:
    """Центральная конфигурация безопасности."""

    # ─── PII Tokenizer ────────────────────────────────────────
    PII_TOKEN_TTL_SECONDS: int = 3600        # TTL маппинга в Redis (1 час)
    PII_REDIS_PREFIX: str = "pii:"

    # ─── Guardrails ───────────────────────────────────────────
    MAX_PAYLOAD_LENGTH: int = 2000           # Макс. длина пользовательского сообщения
    RATE_LIMIT_PER_MINUTE: int = 10          # Лимит запросов на сессию/мин
    RATE_LIMIT_REDIS_PREFIX: str = "ratelimit:"
    ENABLE_LLM_GUARDRAIL: bool = False       # LLM-проверка подозрительных запросов
    LLM_GUARDRAIL_THRESHOLD: float = 0.5     # Порог для LLM-check

    # ─── Injection-паттерны (rule-based) ──────────────────────
    INJECTION_PATTERNS: List[str] = field(default_factory=lambda: [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"ignore\s+(all\s+)?above",
        r"disregard\s+(all\s+)?previous",
        r"forget\s+(all\s+)?previous",
        r"you\s+are\s+now",
        r"new\s+instructions?\s*:",
        r"system\s*:",
        r"<\|im_start\|>",
        r"\[INST\]",
        r"\[/INST\]",
        r"<\|system\|>",
        r"<\|user\|>",
        r"<\|assistant\|>",
        r"print\s+your\s+(system\s+)?prompt",
        r"show\s+(me\s+)?your\s+(system\s+)?prompt",
        r"reveal\s+(your\s+)?(system\s+)?instructions",
        r"what\s+(is|are)\s+your\s+(system\s+)?(prompt|instructions)",
        r"repeat\s+(the\s+)?(text|words|instructions)\s+above",
        r"ignore\s+everything\s+(before|above)",
        r"override\s+(previous\s+)?instructions",
        r"jailbreak",
        r"DAN\s+mode",
    ])

    # ─── Credential Broker ────────────────────────────────────
    CRED_REDIS_PREFIX: str = "cred:"
    CRED_TTL_SECONDS: int = 3600

    # ─── Audit ────────────────────────────────────────────────
    AUDIT_LOG_FILE: str = "logs/audit.jsonl"
    AUDIT_MASK_PII: bool = True

    # ─── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ─── Защищённые API-пути ──────────────────────────────────
    PROTECTED_PATHS: List[str] = field(default_factory=lambda: [
        "/api/chat",
        "/api/plan",
        "/api/travel",
    ])

    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Загрузка конфигурации из переменных окружения."""
        return cls(
            PII_TOKEN_TTL_SECONDS=int(os.getenv("PII_TOKEN_TTL_SECONDS", "3600")),
            MAX_PAYLOAD_LENGTH=int(os.getenv("MAX_PAYLOAD_LENGTH", "2000")),
            RATE_LIMIT_PER_MINUTE=int(os.getenv("RATE_LIMIT_PER_MINUTE", "10")),
            ENABLE_LLM_GUARDRAIL=os.getenv("ENABLE_LLM_GUARDRAIL", "false").lower() == "true",
            LLM_GUARDRAIL_THRESHOLD=float(os.getenv("LLM_GUARDRAIL_THRESHOLD", "0.5")),
            REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:6379"),
            AUDIT_LOG_FILE=os.getenv("AUDIT_LOG_FILE", "logs/audit.jsonl"),
        )


# Singleton — импортируй и используй: from app.security.config import config
config = SecurityConfig.from_env()
