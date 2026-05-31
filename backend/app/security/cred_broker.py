"""
Credential Broker для Halyk Travel Companion.

Управляет партнёрскими API-ключами и токенами.
Модель НИКОГДА не видит эти ключи — они подставляются
сервисным слоем при вызове партнёрских API.

Принцип: агент запрашивает «найди такси», а cred_broker
сам подставляет auth header для inDrive API.
"""

import os
import json
import logging
from typing import Optional, Dict
from dataclasses import dataclass

import redis.asyncio as aioredis

from .config import config

logger = logging.getLogger("security.cred_broker")


@dataclass
class PartnerCredential:
    """Учётные данные партнёрского API."""
    partner: str
    api_key: str
    api_url: str
    extra_headers: Dict[str, str]


# ─── Конфигурация партнёров (из env) ─────────────────────────

PARTNER_ENV_MAP = {
    "indrive": {
        "key_env": "INDRIVE_API_KEY",
        "url_env": "INDRIVE_API_URL",
        "default_url": "https://api.indrive.com/v1",
    },
    "kino": {
        "key_env": "KINO_API_KEY",
        "url_env": "KINO_API_URL",
        "default_url": "https://api.kino.kz/v1",
    },
    "pharmacy": {
        "key_env": "PHARMACY_API_KEY",
        "url_env": "PHARMACY_API_URL",
        "default_url": "https://api.pharmacy.kz/v1",
    },
    "halyk_pay": {
        "key_env": "HALYK_PAY_API_KEY",
        "url_env": "HALYK_PAY_API_URL",
        "default_url": "https://api.halykbank.kz/pay/v1",
    },
    "flights": {
        "key_env": "FLIGHTS_API_KEY",
        "url_env": "FLIGHTS_API_URL",
        "default_url": "https://api.halyktravel.kz/flights/v1",
    },
    "hotels": {
        "key_env": "HOTELS_API_KEY",
        "url_env": "HOTELS_API_URL",
        "default_url": "https://api.halyktravel.kz/hotels/v1",
    },
}


class CredentialBroker:
    """
    Безопасное управление партнёрскими ключами.

    Ключи загружаются из переменных окружения, кэшируются в Redis.
    LLM никогда не видит ключи — они подставляются при исполнении
    tool-вызова.

    Использование:
        broker = CredentialBroker(redis_client)

        # Получить credentials для inDrive
        cred = await broker.get_credential("indrive")
        headers = broker.build_auth_headers(cred)
        # → {"Authorization": "Bearer sk-indrive-...", "Content-Type": "application/json"}
    """

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client
        self.prefix = config.CRED_REDIS_PREFIX
        self.ttl = config.CRED_TTL_SECONDS
        self._cache: Dict[str, PartnerCredential] = {}

    async def get_credential(self, partner: str) -> Optional[PartnerCredential]:
        """
        Получить учётные данные для партнёра.

        Args:
            partner: Имя партнёра (indrive, kino, pharmacy, halyk_pay, flights, hotels)

        Returns:
            PartnerCredential или None если не настроен.
        """
        # 1. Кэш в памяти
        if partner in self._cache:
            return self._cache[partner]

        # 2. Redis кэш
        if self.redis:
            cached = await self._load_from_redis(partner)
            if cached:
                self._cache[partner] = cached
                return cached

        # 3. Из env
        cred = self._load_from_env(partner)
        if cred:
            self._cache[partner] = cred
            if self.redis:
                await self._store_to_redis(partner, cred)
            return cred

        logger.warning(f"No credentials found for partner: {partner}")
        return None

    def _load_from_env(self, partner: str) -> Optional[PartnerCredential]:
        """Загружает ключи из переменных окружения."""
        partner_config = PARTNER_ENV_MAP.get(partner)
        if not partner_config:
            logger.warning(f"Unknown partner: {partner}")
            return None

        api_key = os.getenv(partner_config["key_env"])
        if not api_key:
            # Для хакатона — используем мок-ключ
            api_key = f"mock_{partner}_key_for_hackathon"
            logger.info(
                f"Using mock API key for {partner} "
                f"(set {partner_config['key_env']} for real key)"
            )

        api_url = os.getenv(
            partner_config["url_env"],
            partner_config["default_url"],
        )

        return PartnerCredential(
            partner=partner,
            api_key=api_key,
            api_url=api_url,
            extra_headers={},
        )

    async def _store_to_redis(self, partner: str, cred: PartnerCredential):
        """Кэширует credentials в Redis."""
        key = f"{self.prefix}{partner}"
        data = json.dumps({
            "partner": cred.partner,
            "api_key": cred.api_key,
            "api_url": cred.api_url,
            "extra_headers": cred.extra_headers,
        })
        await self.redis.set(key, data, ex=self.ttl)

    async def _load_from_redis(self, partner: str) -> Optional[PartnerCredential]:
        """Загружает credentials из Redis."""
        key = f"{self.prefix}{partner}"
        data = await self.redis.get(key)
        if not data:
            return None
        parsed = json.loads(data)
        return PartnerCredential(**parsed)

    @staticmethod
    def build_auth_headers(cred: PartnerCredential) -> Dict[str, str]:
        """
        Создаёт HTTP-заголовки для партнёрского API.

        Возвращает dict с Authorization и Content-Type.
        LLM эти заголовки не видит.
        """
        headers = {
            "Authorization": f"Bearer {cred.api_key}",
            "Content-Type": "application/json",
        }
        headers.update(cred.extra_headers)
        return headers

    def list_partners(self) -> list[str]:
        """Список доступных партнёров."""
        return list(PARTNER_ENV_MAP.keys())

    async def refresh_credential(self, partner: str) -> Optional[PartnerCredential]:
        """Принудительное обновление credentials из env."""
        # Удаляем из кэшей
        self._cache.pop(partner, None)
        if self.redis:
            key = f"{self.prefix}{partner}"
            await self.redis.delete(key)

        # Перезагружаем
        return await self.get_credential(partner)
