"""Тесты авторизации — регистрация, вход, токены."""

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


# === Тесты сервиса авторизации ===

class TestAuthService:
    """Тесты бизнес-логики авторизации."""

    def test_hash_password(self):
        """Хеширование пароля работает корректно."""
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Проверка правильного пароля."""
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_password_wrong(self):
        """Проверка неправильного пароля."""
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self):
        """Создание access-токена."""
        token = create_access_token(user_id=42)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Создание refresh-токена."""
        token = create_refresh_token(user_id=42)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Декодирование валидного токена."""
        token = create_access_token(user_id=42)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["type"] == "access"

    def test_decode_refresh_token(self):
        """Декодирование refresh-токена."""
        token = create_refresh_token(user_id=42)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        """Декодирование невалидного токена возвращает None."""
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_decode_empty_token(self):
        """Декодирование пустого токена возвращает None."""
        payload = decode_token("")
        assert payload is None


# === Тесты API авторизации ===

class TestAuthAPI:
    """Тесты эндпоинтов авторизации."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Успешная регистрация нового пользователя."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@test.com",
            "password": "password123",
            "full_name": "Новый Пользователь",
            "role": "student",
        })
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == "newuser@test.com"
        assert data["user"]["full_name"] == "Новый Пользователь"
        assert data["user"]["role"] == "student"
        assert data["tokens"]["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Регистрация с существующим email возвращает 409."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "student@test.com",
            "password": "password123",
            "full_name": "Дубликат",
            "role": "student",
        })
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Регистрация с невалидным email возвращает 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Тест",
            "role": "student",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Регистрация с коротким паролем возвращает 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@test.com",
            "password": "123",
            "full_name": "Тест",
            "role": "student",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Успешный вход."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "student@test.com",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "student@test.com"
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Вход с неверным паролем возвращает 401."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "student@test.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Вход несуществующего пользователя возвращает 401."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nobody@test.com",
            "password": "password123",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, test_user: User):
        """Обновление токена по refresh-токену."""
        refresh = create_refresh_token(test_user.id)
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(self, client: AsyncClient, test_user: User):
        """Использование access-токена вместо refresh возвращает 401."""
        access = create_access_token(test_user.id)
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": access,
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient):
        """Выход из системы."""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200
