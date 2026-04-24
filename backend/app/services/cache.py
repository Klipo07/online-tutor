"""Сервис кэширования на базе Redis.

Простая обёртка над `redis.asyncio` с JSON-сериализацией.
Если REDIS_URL пуст или Redis недоступен — операции тихо деградируют (cache miss),
сервер продолжает работать напрямую с БД.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

# Версионируем префикс, чтобы при ломающих изменениях формата
# достаточно было инкрементнуть версию без FLUSHDB
_PREFIX = "ai_tutor:v1:"

_client: aioredis.Redis | None = None


def _get_client() -> aioredis.Redis | None:
    """Лениво создаём подключение к Redis."""
    global _client
    if _client is not None:
        return _client
    url = settings.REDIS_URL
    if not url:
        return None
    _client = aioredis.from_url(url, encoding="utf-8", decode_responses=True)
    return _client


async def get(key: str) -> Any | None:
    """Прочитать JSON из кэша или вернуть None."""
    client = _get_client()
    if client is None:
        return None
    try:
        raw = await client.get(_PREFIX + key)
    except Exception as e:
        logger.warning("Redis GET failed (%s): %s", key, e)
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def set(key: str, value: Any, ttl: int) -> None:
    """Записать JSON-сериализуемое значение с TTL в секундах."""
    client = _get_client()
    if client is None:
        return
    try:
        await client.set(_PREFIX + key, json.dumps(value, default=str), ex=ttl)
    except Exception as e:
        logger.warning("Redis SET failed (%s): %s", key, e)


async def delete(*keys: str) -> None:
    """Удалить ключи из кэша."""
    client = _get_client()
    if client is None or not keys:
        return
    try:
        await client.delete(*(_PREFIX + k for k in keys))
    except Exception as e:
        logger.warning("Redis DEL failed: %s", e)


async def delete_pattern(pattern: str) -> None:
    """Удалить все ключи по шаблону (для инвалидации целой группы кэшей)."""
    client = _get_client()
    if client is None:
        return
    try:
        full_pattern = _PREFIX + pattern
        keys: list[str] = []
        async for key in client.scan_iter(match=full_pattern, count=200):
            keys.append(key)
        if keys:
            await client.delete(*keys)
    except Exception as e:
        logger.warning("Redis SCAN/DEL failed (%s): %s", pattern, e)


async def incr_with_ttl(key: str, ttl: int) -> int:
    """Атомарный INCR c установкой TTL при первом инкременте.

    Нужен для rate-limit: одна операция INCR + EXPIRE.
    При недоступности Redis возвращаем 1 (как будто запрос первый).
    """
    client = _get_client()
    if client is None:
        return 1
    try:
        pipe = client.pipeline()
        pipe.incr(_PREFIX + key)
        pipe.expire(_PREFIX + key, ttl)
        results = await pipe.execute()
        return int(results[0])
    except Exception as e:
        logger.warning("Redis INCR failed (%s): %s", key, e)
        return 1


async def close() -> None:
    """Закрыть соединение (вызываем на shutdown)."""
    global _client
    if _client is not None:
        try:
            await _client.close()
        finally:
            _client = None
