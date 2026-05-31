"""
Halyk Travel Companion — Security Module.

Слой безопасности: токенизация ПДн, guardrails, credential broker, audit.

Быстрый старт (в main.py):

    import redis.asyncio as aioredis
    from app.security import (
        PIITokenizer,
        GuardrailChecker,
        GuardrailMiddleware,
        AuditMiddleware,
        CredentialBroker,
        audit_logger,
        config,
    )

    # Redis
    redis_client = aioredis.from_url(config.REDIS_URL)

    # Компоненты безопасности
    tokenizer = PIITokenizer(redis_client)
    guardrail = GuardrailChecker(redis_client)
    cred_broker = CredentialBroker(redis_client)

    # Middleware (порядок важен: audit → guardrail)
    app.add_middleware(AuditMiddleware)
    app.add_middleware(GuardrailMiddleware, checker=guardrail)
"""

from .config import SecurityConfig, config
from .tokenizer import PIITokenizer, mask_pii_for_logs
from .guardrails import GuardrailChecker, GuardrailResult, GuardrailVerdict
from .guardrail_middleware import GuardrailMiddleware
from .cred_broker import CredentialBroker, PartnerCredential
from .audit import AuditLogger, AuditAction, audit_logger
from .audit_middleware import AuditMiddleware

# ─── Phase 4: Hardening ──────────────────────────────────────
from .hardening import SecurityHeadersMiddleware, setup_cors, setup_security
from .env_checker import run_security_checks, SecurityCheckResult
from .prompt_shield import PromptShield
from .session import SessionManager, SessionInfo

__all__ = [
    # Config
    "SecurityConfig",
    "config",
    # Tokenizer
    "PIITokenizer",
    "mask_pii_for_logs",
    # Guardrails
    "GuardrailChecker",
    "GuardrailResult",
    "GuardrailVerdict",
    "GuardrailMiddleware",
    # Credentials
    "CredentialBroker",
    "PartnerCredential",
    # Audit
    "AuditLogger",
    "AuditAction",
    "audit_logger",
    "AuditMiddleware",
    # Hardening (Phase 4)
    "SecurityHeadersMiddleware",
    "setup_cors",
    "setup_security",
    "run_security_checks",
    "SecurityCheckResult",
    "PromptShield",
    "SessionManager",
    "SessionInfo",
]
