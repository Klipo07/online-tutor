"""Тесты пользователей — профиль, обновление, прогресс, статистика."""

import pytest
from httpx import AsyncClient

from app.models.user import User


class TestUsersAPI:
    """Тесты эндпоинтов пользователей."""

    @pytest.mark.asyncio
    async def test_get_profile(self, client: AsyncClient, test_user: User, auth_headers: dict):
        """Получение профиля авторизованного пользователя."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "student@test.com"
        assert data["full_name"] == "Иван Тестов"
        assert data["role"] == "student"

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, client: AsyncClient):
        """Запрос профиля без токена — отказано (HTTPBearer возвращает 403)."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_update_profile(self, client: AsyncClient, test_user: User, auth_headers: dict):
        """Обновление профиля пользователя."""
        response = await client.put("/api/v1/users/me", json={
            "first_name": "Иван",
            "last_name": "Обновлённый",
            "phone": "+79991234567",
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Иван Обновлённый"
        assert data["first_name"] == "Иван"
        assert data["last_name"] == "Обновлённый"
        assert data["phone"] == "+79991234567"

    @pytest.mark.asyncio
    async def test_update_profile_empty(self, client: AsyncClient, test_user: User, auth_headers: dict):
        """Обновление без данных возвращает 400."""
        response = await client.put("/api/v1/users/me", json={}, headers=auth_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_progress_empty(self, client: AsyncClient, test_user: User, auth_headers: dict):
        """Прогресс нового пользователя — пустой."""
        response = await client.get("/api/v1/users/me/progress", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["progress"] == []

    @pytest.mark.asyncio
    async def test_get_stats(self, client: AsyncClient, test_user: User, auth_headers: dict):
        """Статистика нового пользователя — нули."""
        response = await client.get("/api/v1/users/me/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["tests_completed"] == 0
        assert data["average_score"] == 0
        assert data["chat_sessions"] == 0

    @pytest.mark.asyncio
    async def test_get_test_history_empty(self, client: AsyncClient, test_user: User, auth_headers: dict):
        """История тестов нового пользователя — пустая."""
        response = await client.get("/api/v1/users/me/test-history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["history"] == []
