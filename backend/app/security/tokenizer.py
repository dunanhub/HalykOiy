"""
PII Tokenizer для Halyk Travel Companion.

Обнаруживает и заменяет персональные данные на безопасные токены
перед отправкой в LLM. Поддерживает обратную детокенизацию через Redis.

Казахстанские ПДн:
  - ИИН (12 цифр)
  - Телефон (+7 7xx xxx xx xx)
  - Банковская карта (16 цифр)
  - Паспорт (1 буква + 8 цифр)
  - Email
  - ФИО (кириллица)
"""

import re
import uuid
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import redis.asyncio as aioredis

from .config import config

logger = logging.getLogger("security.tokenizer")


# ─── Data classes ─────────────────────────────────────────────

@dataclass
class PIIMatch:
    """Обнаруженное совпадение ПДн."""
    pii_type: str
    original: str
    token: str
    start: int
    end: int


# ─── Паттерны обнаружения ─────────────────────────────────────

PII_PATTERNS = {
    # Карта первой — 16 цифр не должны ложно попасть в ИИН (12 цифр)
    "CARD": re.compile(
        r"\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b"
    ),
    "IIN": re.compile(
        r"\b(\d{12})\b"
    ),
    "PHONE": re.compile(
        r"(\+?7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})"
    ),
    "EMAIL": re.compile(
        r"\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b"
    ),
    "PASSPORT": re.compile(
        r"\b([A-Z]\d{8})\b"
    ),
}

# Кириллические имена: 2-3 слова с заглавной буквы подряд
CYRILLIC_NAME_PATTERN = re.compile(
    r"(?<!\w)([А-ЯЁ][а-яё]{1,20}(?:\s+[А-ЯЁ][а-яё]{1,20}){1,2})(?!\w)"
)

# Слова, которые НЕ являются именами (города, дни недели и т.д.)
NOT_NAMES: set = {
    # Города Казахстана
    "Алматы", "Астана", "Шымкент", "Караганда", "Актау", "Атырау",
    "Павлодар", "Семей", "Кокшетау", "Тараз", "Костанай", "Уральск",
    "Петропавловск", "Актобе", "Кызылорда", "Туркестан", "Талдыкорган",
    "Темиртау", "Экибастуз", "Рудный", "Жезказган", "Балхаш",
    "Байконур", "Степногорск", "Сатпаев", "Риддер", "Аксай",
    # Курорты
    "Боровое", "Бурабай", "Капчагай", "Алаколь", "Чарын",
    # Города СНГ / мира
    "Москва", "Россия", "Казахстан", "Ташкент", "Бишкек", "Дубай",
    "Стамбул", "Анталья", "Батуми", "Тбилиси",
    # Дни недели
    "Понедельник", "Вторник", "Среда", "Четверг", "Пятница",
    "Суббота", "Воскресенье",
    # Месяцы
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
    # Общие слова
    "Привет", "Здравствуйте", "Спасибо", "Пожалуйста", "Добрый",
    "Хочу", "Нужно", "Можно", "Давай", "Ладно",
    "Поездка", "Семья", "Дети", "Ребёнок", "Ребенок", "Жена", "Муж",
    "Отель", "Билет", "Рейс", "Аэропорт", "Вокзал", "Такси",
    "Страховка", "Аптека", "Бронь", "Бюджет", "Бонус",
    # Авиакомпании
    "Эйр", "Флай",
}


def _generate_token(pii_type: str) -> str:
    """Генерирует уникальный токен для типа ПДн."""
    short_id = uuid.uuid4().hex[:6]
    return f"[{pii_type}_{short_id}]"


def _is_part_of_longer_number(text: str, start: int, end: int) -> bool:
    """Проверяет, является ли число частью более длинного числа."""
    if start > 0 and text[start - 1].isdigit():
        return True
    if end < len(text) and text[end].isdigit():
        return True
    return False


class PIITokenizer:
    """
    Обнаруживает и токенизирует ПДн в тексте перед отправкой в LLM.
    Хранит маппинг token→original в Redis для обратной детокенизации.

    Использование:
        tokenizer = PIITokenizer(redis_client)
        clean_text, session_id = await tokenizer.tokenize("Я Иванов Иван, ИИН 010203456789")
        # clean_text: "Я [NAME_a1b2c3], ИИН [IIN_d4e5f6]"
        # ... отправляем clean_text в LLM ...
        restored = await tokenizer.detokenize(llm_response, session_id)
    """

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.ttl = config.PII_TOKEN_TTL_SECONDS
        self.prefix = config.PII_REDIS_PREFIX

    def detect_pii(self, text: str) -> List[PIIMatch]:
        """
        Обнаруживает все экземпляры ПДн в тексте.
        Возвращает список PIIMatch, отсортированный по позиции (с конца).
        """
        matches: List[PIIMatch] = []
        matched_ranges: List[Tuple[int, int]] = []

        # 1. Regex-паттерны (CARD первым чтобы 16-цифр не попали в IIN)
        for pii_type, pattern in PII_PATTERNS.items():
            for match in pattern.finditer(text):
                value = match.group(1)
                start = match.start(1)
                end = match.end(1)

                # Пропускаем ИИН если часть длинного числа
                if pii_type == "IIN" and _is_part_of_longer_number(text, start, end):
                    continue

                # Пропускаем если уже покрыто другим паттерном (CARD vs IIN)
                if any(s <= start and end <= e for s, e in matched_ranges):
                    continue

                token = _generate_token(pii_type)
                matches.append(PIIMatch(
                    pii_type=pii_type,
                    original=value,
                    token=token,
                    start=start,
                    end=end,
                ))
                matched_ranges.append((start, end))

        # 2. Кириллические имена (эвристика)
        for match in CYRILLIC_NAME_PATTERN.finditer(text):
            name = match.group(1)
            start = match.start(1)
            end = match.end(1)
            words = name.split()

            # Пропускаем если любое слово — в списке НЕ-имён
            if any(w in NOT_NAMES for w in words):
                continue

            # Пропускаем одиночные короткие слова
            if len(words) == 1 and len(words[0]) < 4:
                continue

            # Пропускаем если пересекается с уже найденным
            if any(not (end <= s or start >= e) for s, e in matched_ranges):
                continue

            token = _generate_token("NAME")
            matches.append(PIIMatch(
                pii_type="NAME",
                original=name,
                token=token,
                start=start,
                end=end,
            ))
            matched_ranges.append((start, end))

        # Сортируем с конца для безопасной замены
        matches.sort(key=lambda m: m.start, reverse=True)
        return matches

    async def tokenize(
        self,
        text: str,
        session_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Заменяет все ПДн в тексте на токены.

        Args:
            text: Исходный текст с ПДн.
            session_id: Опциональный ID сессии. Если не указан — генерируется.

        Returns:
            Tuple[str, str]: (очищенный_текст, session_id)
        """
        if session_id is None:
            session_id = uuid.uuid4().hex

        matches = self.detect_pii(text)
        if not matches:
            return text, session_id

        mapping: Dict[str, str] = {}
        result = text

        for m in matches:
            result = result[:m.start] + m.token + result[m.end:]
            mapping[m.token] = m.original
            logger.info(
                f"Tokenized {m.pii_type}: "
                f"{'*' * min(len(m.original), 20)} → {m.token}"
            )

        # Сохраняем маппинг в Redis
        await self._store_mapping(session_id, mapping)

        return result, session_id

    async def detokenize(self, text: str, session_id: str) -> str:
        """
        Восстанавливает ПДн из токенов, используя маппинг из Redis.

        Args:
            text: Текст с токенами (от LLM).
            session_id: ID сессии для получения маппинга.

        Returns:
            str: Текст с восстановленными ПДн.
        """
        mapping = await self._load_mapping(session_id)
        if not mapping:
            logger.warning(f"No PII mapping found for session {session_id}")
            return text

        result = text
        for token, original in mapping.items():
            result = result.replace(token, original)

        return result

    async def _store_mapping(self, session_id: str, mapping: Dict[str, str]):
        """Сохраняет маппинг token→PII в Redis с TTL."""
        key = f"{self.prefix}{session_id}"
        await self.redis.set(
            key,
            json.dumps(mapping, ensure_ascii=False),
            ex=self.ttl,
        )
        logger.debug(f"Stored {len(mapping)} PII mappings, session={session_id}")

    async def _load_mapping(self, session_id: str) -> Dict[str, str]:
        """Загружает маппинг token→PII из Redis."""
        key = f"{self.prefix}{session_id}"
        data = await self.redis.get(key)
        if data is None:
            return {}
        return json.loads(data)

    async def clear_session(self, session_id: str):
        """Явная очистка данных ПДн для сессии."""
        key = f"{self.prefix}{session_id}"
        await self.redis.delete(key)
        logger.info(f"Cleared PII session {session_id}")


# ─── Утилита: быстрая маскировка для логов (без Redis) ────────

def mask_pii_for_logs(text: str) -> str:
    """
    Быстрая однонаправленная маскировка ПДн для логов.
    НЕ использует Redis, НЕ обратима. Для аудит-логов.
    """
    result = text

    for pii_type, pattern in PII_PATTERNS.items():
        result = pattern.sub(f"[{pii_type}_MASKED]", result)

    # Кириллические имена
    for match in CYRILLIC_NAME_PATTERN.finditer(result):
        name = match.group(1)
        words = name.split()
        if any(w in NOT_NAMES for w in words):
            continue
        if len(words) == 1 and len(words[0]) < 4:
            continue
        result = result.replace(name, "[NAME_MASKED]", 1)

    return result
