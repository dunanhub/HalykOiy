"""
Session Security для Halyk Travel.

Криптографически стойкие сессии с TTL, привязкой к IP
и автоматическим истечением.

Использование:
    from app.security.session import SessionManager

    session_mgr = SessionManager(redis_client)

    # Создать сессию
    session = await session_mgr.create_session(ip="1.2.3.4", user_agent="...")

    # Проверить сессию
    is_valid, info = await session_mgr.validate_session(session.session_id, ip="1.2.3.4")

    # Завершить сессию
    await session_mgr.destroy_session(session.session_id)
"""

import json
import secrets
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict
from dataclasses import dataclass, asdict

logger = logging.getLogger("security.session")


# ─── Конфигурация ─────────────────────────────────────────────

SESSION_TTL_SECONDS = 1800          # 30 мин неактивности
SESSION_ABSOLUTE_TTL = 86400        # 24 часа абсолютный максимум
SESSION_ID_LENGTH = 32              # 256 бит энтропии
SESSION_REDIS_PREFIX = "session:"
BIND_TO_IP = False                  # Привязка к IP (опционально)


@dataclass
class SessionInfo:
    """Метаданные сессии."""
    session_id: str
    ip: str
    user_agent: str
    created_at: str
    last_active: str
    request_count: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "SessionInfo":
        return cls(**json.loads(data))


class SessionManager:
    """
    Управление сессиями.

    - Криптографически стойкие ID (secrets.token_urlsafe)
    - TTL 30 мин неактивности (продлевается при каждом запросе)
    - Абсолютный TTL 24 часа (не продлевается)
    - Опциональная привязка к IP
    """

    def __init__(
        self,
        redis_client=None,
        ttl: int = SESSION_TTL_SECONDS,
        absolute_ttl: int = SESSION_ABSOLUTE_TTL,
        bind_ip: bool = BIND_TO_IP,
    ):
        self.redis = redis_client
        self.ttl = ttl
        self.absolute_ttl = absolute_ttl
        self.bind_ip = bind_ip
        self.prefix = SESSION_REDIS_PREFIX

    def _generate_session_id(self) -> str:
        """Генерирует криптостойкий session ID."""
        return secrets.token_urlsafe(SESSION_ID_LENGTH)  # 256 бит

    async def create_session(
        self,
        ip: str = "unknown",
        user_agent: str = "unknown",
    ) -> SessionInfo:
        """
        Создаёт новую сессию.

        Returns:
            SessionInfo с уникальным session_id.
        """
        now = datetime.now(timezone.utc).isoformat()
        session = SessionInfo(
            session_id=self._generate_session_id(),
            ip=ip,
            user_agent=user_agent[:200],  # Обрезаем длинные UA
            created_at=now,
            last_active=now,
            request_count=0,
        )

        if self.redis:
            key = f"{self.prefix}{session.session_id}"
            await self.redis.set(key, session.to_json(), ex=self.ttl)

        logger.info(f"Session created: {session.session_id[:16]}... ip={ip}")
        return session

    async def validate_session(
        self,
        session_id: str,
        ip: str = "unknown",
    ) -> Tuple[bool, Optional[SessionInfo]]:
        """
        Проверяет и обновляет сессию.

        Проверяет:
        1. Сессия существует в Redis
        2. Не истекла (абсолютный TTL)
        3. IP совпадает (если bind_ip включён)

        При успехе — продлевает TTL и увеличивает request_count.

        Returns:
            (is_valid, session_info)
        """
        if not self.redis:
            # Без Redis — пропускаем (dev mode)
            return True, None

        key = f"{self.prefix}{session_id}"
        data = await self.redis.get(key)

        if not data:
            logger.warning(f"Session not found or expired: {session_id[:16]}...")
            return False, None

        session = SessionInfo.from_json(data)

        # Проверяем абсолютный TTL
        created = datetime.fromisoformat(session.created_at)
        now = datetime.now(timezone.utc)
        age_seconds = (now - created).total_seconds()

        if age_seconds > self.absolute_ttl:
            logger.warning(
                f"Session absolute TTL expired: {session_id[:16]}... "
                f"age={age_seconds:.0f}s"
            )
            await self.destroy_session(session_id)
            return False, None

        # Проверяем IP (если включена привязка)
        if self.bind_ip and session.ip != ip:
            logger.warning(
                f"Session IP mismatch: {session_id[:16]}... "
                f"expected={session.ip}, got={ip}"
            )
            return False, None

        # Обновляем last_active и request_count
        session.last_active = now.isoformat()
        session.request_count += 1

        # Продлеваем TTL
        await self.redis.set(key, session.to_json(), ex=self.ttl)

        return True, session

    async def destroy_session(self, session_id: str) -> bool:
        """Удаляет сессию."""
        if self.redis:
            key = f"{self.prefix}{session_id}"
            deleted = await self.redis.delete(key)
            if deleted:
                logger.info(f"Session destroyed: {session_id[:16]}...")
                return True
        return False

    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Получить информацию о сессии без обновления."""
        if not self.redis:
            return None

        key = f"{self.prefix}{session_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        return SessionInfo.from_json(data)

    async def get_active_sessions_count(self) -> int:
        """Количество активных сессий (приблизительно)."""
        if not self.redis:
            return 0

        cursor = 0
        count = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor, match=f"{self.prefix}*", count=100
            )
            count += len(keys)
            if cursor == 0:
                break
        return count
