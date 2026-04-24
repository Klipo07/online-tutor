"""Тесты кэш-инвалидации: убеждаемся что PATCH/review/schedule сбрасывают закэшированный маркетплейс.

Redis в тестах недоступен (SQLite in-memory среда), поэтому подменяем
`app.services.cache.*` на in-memory fake с поддержкой delete_pattern через fnmatch.
Это честный тест поведения роутера — он вызывает cache.get/set/delete,
нам остаётся проверить что после мутации чтение больше не попадает в кэш.
"""

from __future__ import annotations

import fnmatch
import json
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import cache as real_cache
from app.models.tutor import TutorProfile
from app.models.user import User


class _FakeCache:
    """Простой in-memory заменитель Redis для тестов.

    Повторяет контракт app.services.cache: get/set/delete/delete_pattern/incr_with_ttl.
    TTL игнорируем — в тестах он не важен.
    """

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> Any | None:
        raw = self.store.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int) -> None:
        self.store[key] = json.dumps(value, default=str)

    async def delete(self, *keys: str) -> None:
        for k in keys:
            self.store.pop(k, None)

    async def delete_pattern(self, pattern: str) -> None:
        # fnmatch — glob-style (* и ?) как в Redis SCAN MATCH
        matched = [k for k in list(self.store.keys()) if fnmatch.fnmatch(k, pattern)]
        for k in matched:
            self.store.pop(k, None)

    async def incr_with_ttl(self, key: str, ttl: int) -> int:
        val = int(self.store.get(key, "0")) + 1
        self.store[key] = str(val)
        return val


@pytest_asyncio.fixture
async def fake_cache(monkeypatch: pytest.MonkeyPatch) -> _FakeCache:
    """Заменяем real_cache.* на методы in-memory фейка."""
    fake = _FakeCache()
    monkeypatch.setattr(real_cache, "get", fake.get)
    monkeypatch.setattr(real_cache, "set", fake.set)
    monkeypatch.setattr(real_cache, "delete", fake.delete)
    monkeypatch.setattr(real_cache, "delete_pattern", fake.delete_pattern)
    monkeypatch.setattr(real_cache, "incr_with_ttl", fake.incr_with_ttl)
    return fake


class TestTutorsCacheInvalidation:
    """Маркетплейс тьюторов: инвалидация при изменении профиля/расписания/отзыва."""

    @pytest.mark.asyncio
    async def test_list_populates_cache_on_first_call(
        self,
        client: AsyncClient,
        test_tutor_profile: TutorProfile,
        fake_cache: _FakeCache,
    ):
        """Первый GET /tutors/ кладёт ответ в кэш."""
        assert fake_cache.store == {}
        r1 = await client.get("/api/v1/tutors/")
        assert r1.status_code == 200
        # Ключ содержит параметры фильтров — проверяем что создался хотя бы один "tutors:list:*"
        keys = [k for k in fake_cache.store if k.startswith("tutors:list:")]
        assert len(keys) == 1

    @pytest.mark.asyncio
    async def test_patch_profile_invalidates_list_cache(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tutor_user: User,
        test_tutor_profile: TutorProfile,
        tutor_auth_headers: dict,
        fake_cache: _FakeCache,
    ):
        """PATCH /tutors/me/profile сбрасывает все закэшированные списки."""
        # Прогрели кэш
        await client.get("/api/v1/tutors/")
        list_keys_before = [k for k in fake_cache.store if k.startswith("tutors:list:")]
        assert len(list_keys_before) >= 1

        # Мутация профиля должна инвалидировать кэш
        response = await client.patch(
            "/api/v1/tutors/me/profile",
            headers=tutor_auth_headers,
            json={"price_per_hour": 2500},
        )
        assert response.status_code == 200
        list_keys_after = [k for k in fake_cache.store if k.startswith("tutors:list:")]
        assert list_keys_after == []

    @pytest.mark.asyncio
    async def test_cached_list_served_until_invalidation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tutor_user: User,
        test_tutor_profile: TutorProfile,
        tutor_auth_headers: dict,
        fake_cache: _FakeCache,
    ):
        """Пока кэш жив — отдаётся старая цена; после PATCH — новая."""
        # Прогрев — цена 1500
        r1 = await client.get("/api/v1/tutors/")
        assert r1.json()["tutors"][0]["price_per_hour"] == 1500.0

        # Меняем цену в БД напрямую (в обход роутера — чтобы кэш не сбросился)
        test_tutor_profile.price_per_hour = 9999
        db_session.add(test_tutor_profile)
        await db_session.commit()

        # Кэш всё ещё возвращает 1500
        r2 = await client.get("/api/v1/tutors/")
        assert r2.json()["tutors"][0]["price_per_hour"] == 1500.0

        # Теперь PATCH через роутер — сбрасывает кэш
        await client.patch(
            "/api/v1/tutors/me/profile",
            headers=tutor_auth_headers,
            json={"experience_years": 12},
        )
        r3 = await client.get("/api/v1/tutors/")
        assert r3.json()["tutors"][0]["price_per_hour"] == 9999.0

    @pytest.mark.asyncio
    async def test_schedule_update_invalidates_tutor_detail(
        self,
        client: AsyncClient,
        test_tutor_profile: TutorProfile,
        tutor_auth_headers: dict,
        fake_cache: _FakeCache,
    ):
        """PUT /tutors/me/schedule сбрасывает ключ деталей репетитора."""
        detail_key = f"tutors:detail:{test_tutor_profile.id}"
        # Кладём фиктивный ключ — роутер должен его удалить
        fake_cache.store[detail_key] = json.dumps({"stub": True})

        response = await client.put(
            "/api/v1/tutors/me/schedule",
            headers=tutor_auth_headers,
            json={
                "mon": [9, 21], "tue": [9, 21], "wed": [9, 21],
                "thu": [9, 21], "fri": [9, 21], "sat": None, "sun": None,
            },
        )
        assert response.status_code == 200
        assert detail_key not in fake_cache.store

    @pytest.mark.asyncio
    async def test_new_review_invalidates_list_and_detail(
        self,
        client: AsyncClient,
        test_user: User,
        test_tutor_profile: TutorProfile,
        auth_headers: dict,
        fake_cache: _FakeCache,
    ):
        """POST /tutors/{id}/review сбрасывает и список, и детали — рейтинг изменился."""
        # Прогрели кэш списка
        await client.get("/api/v1/tutors/")
        # И фиктивный ключ деталей
        detail_key = f"tutors:detail:{test_tutor_profile.id}"
        fake_cache.store[detail_key] = json.dumps({"stub": True})

        response = await client.post(
            f"/api/v1/tutors/{test_tutor_profile.id}/review",
            headers=auth_headers,
            json={"rating": 5, "comment": "Отличный репетитор, очень понятно объясняет"},
        )
        assert response.status_code == 201

        list_keys = [k for k in fake_cache.store if k.startswith("tutors:list:")]
        assert list_keys == []
        assert detail_key not in fake_cache.store
