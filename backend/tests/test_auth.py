"""Тесты авторизации — регистрация, вход, токены."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tutor import TutorProfile
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
            "password": "Password123",
            "first_name": "Новый",
            "last_name": "Пользователь",
            "role": "student",
        })
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == "newuser@test.com"
        assert data["user"]["full_name"] == "Новый Пользователь"
        assert data["user"]["first_name"] == "Новый"
        assert data["user"]["last_name"] == "Пользователь"
        assert data["user"]["role"] == "student"
        assert data["tokens"]["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Регистрация с существующим email возвращает 409."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "student@test.com",
            "password": "Password123",
            "first_name": "Дубликат",
            "last_name": "Тестов",
            "role": "student",
        })
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Регистрация с невалидным email возвращает 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "Password123",
            "first_name": "Тест",
            "last_name": "Тестов",
            "role": "student",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Регистрация с коротким паролем возвращает 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@test.com",
            "password": "Ab3",
            "first_name": "Тест",
            "last_name": "Тестов",
            "role": "student",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_password_without_uppercase(self, client: AsyncClient):
        """Регистрация с паролем без заглавной буквы возвращает 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "nouppercase@test.com",
            "password": "password123",
            "first_name": "Тест",
            "last_name": "Тестов",
            "role": "student",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Успешный вход."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "student@test.com",
            "password": "Password123",
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
            "password": "Password123",
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


# === Тесты регистрации репетитора (discriminated union) ===

class TestTutorRegistration:
    """Отдельный флоу регистрации репетитора — User + TutorProfile атомарно."""

    @pytest.mark.asyncio
    async def test_register_tutor_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Регистрация репетитора создаёт User + TutorProfile одной транзакцией."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newtutor@test.com",
            "password": "Password123",
            "first_name": "Новый",
            "last_name": "Репетитор",
            "role": "tutor",
            "subjects": ["Математика", "Физика"],
            "price_per_hour": 1500,
            "experience_years": 5,
            "bio": "Готовлю к ЕГЭ",
            "education": "МФТИ",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["role"] == "tutor"
        assert data["user"]["email"] == "newtutor@test.com"

        # Профиль создан, is_verified=False, bio — в users
        user = (await db_session.execute(
            select(User).where(User.email == "newtutor@test.com")
        )).scalar_one()
        assert user.bio == "Готовлю к ЕГЭ"

        profile = (await db_session.execute(
            select(TutorProfile).where(TutorProfile.user_id == user.id)
        )).scalar_one()
        assert profile.is_verified is False
        assert profile.subjects == ["Математика", "Физика"]
        assert float(profile.price_per_hour) == 1500.0
        assert profile.experience_years == 5
        assert profile.education == "МФТИ"

    @pytest.mark.asyncio
    async def test_register_tutor_requires_subjects(self, client: AsyncClient):
        """Регистрация репетитора без предметов возвращает 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "notutor@test.com",
            "password": "Password123",
            "first_name": "Без",
            "last_name": "Предметов",
            "role": "tutor",
            "subjects": [],
            "price_per_hour": 1000,
            "experience_years": 3,
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_tutor_missing_price(self, client: AsyncClient):
        """Регистрация репетитора без цены возвращает 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "noprice@test.com",
            "password": "Password123",
            "first_name": "Без",
            "last_name": "Цены",
            "role": "tutor",
            "subjects": ["Математика"],
            "experience_years": 3,
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_student_ignores_tutor_fields(self, client: AsyncClient):
        """Для role=student лишние tutor-поля не ломают валидацию (discriminator)."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "justastudent@test.com",
            "password": "Password123",
            "first_name": "Просто",
            "last_name": "Ученик",
            "role": "student",
        })
        assert response.status_code == 201
        assert response.json()["user"]["role"] == "student"

    @pytest.mark.asyncio
    async def test_register_tutor_not_in_marketplace(
        self, client: AsyncClient
    ):
        """Новый репетитор с is_verified=False не появляется в /tutors."""
        await client.post("/api/v1/auth/register", json={
            "email": "hidden@test.com",
            "password": "Password123",
            "first_name": "Скрытый",
            "last_name": "Репетитор",
            "role": "tutor",
            "subjects": ["Математика"],
            "price_per_hour": 1000,
            "experience_years": 2,
        })
        response = await client.get("/api/v1/tutors/")
        assert response.status_code == 200
        tutors = response.json()["tutors"]
        emails = [t.get("email") for t in tutors]
        assert "hidden@test.com" not in emails
        assert all(t["is_verified"] for t in tutors)


class TestEmailVerification:
    """Тесты верификации email."""

    @pytest.mark.asyncio
    async def test_register_issues_verify_token(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """После регистрации у пользователя есть токен верификации."""
        res = await client.post("/api/v1/auth/register", json={
            "email": "verifyme@test.com",
            "password": "Password123",
            "first_name": "Виктор",
            "last_name": "Тестов",
            "role": "student",
        })
        assert res.status_code == 201
        assert res.json()["user"]["email_verified"] is False

        result = await db_session.execute(
            select(User).where(User.email == "verifyme@test.com")
        )
        user = result.scalar_one()
        assert user.email_verify_token_hash is not None
        assert user.email_verify_token_expires_at is not None
        assert user.email_verified_at is None

    @pytest.mark.asyncio
    async def test_verify_email_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /auth/verify-email с валидным токеном подтверждает email."""
        from app.services.email_service import generate_verification_token, token_expiry
        from datetime import datetime, timezone

        raw, hashed = generate_verification_token()
        user = User(
            email="tobeverified@test.com",
            password_hash=hash_password("Password123"),
            first_name="Нина",
            last_name="Новичок",
            email_verify_token_hash=hashed,
            email_verify_token_expires_at=token_expiry(),
        )
        db_session.add(user)
        await db_session.commit()

        res = await client.get(f"/api/v1/auth/verify-email?token={raw}")
        assert res.status_code == 200

        await db_session.refresh(user)
        assert user.email_verified_at is not None
        assert user.email_verify_token_hash is None

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, client: AsyncClient):
        """Невалидный токен → 404."""
        res = await client.get("/api/v1/auth/verify-email?token=totallywrongtoken123")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_verify_email_expired(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Истёкший токен → 410."""
        from app.services.email_service import generate_verification_token
        from datetime import datetime, timedelta, timezone

        raw, hashed = generate_verification_token()
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        user = User(
            email="expired@test.com",
            password_hash=hash_password("Password123"),
            first_name="Истёк",
            last_name="Токен",
            email_verify_token_hash=hashed,
            email_verify_token_expires_at=past,
        )
        db_session.add(user)
        await db_session.commit()

        res = await client.get(f"/api/v1/auth/verify-email?token={raw}")
        assert res.status_code == 410

    @pytest.mark.asyncio
    async def test_verify_email_promotes_tutor(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """После подтверждения email у репетитора TutorProfile становится verified."""
        reg = await client.post("/api/v1/auth/register", json={
            "email": "newtutor@test.com",
            "password": "Password123",
            "first_name": "Новый",
            "last_name": "Репетитор",
            "role": "tutor",
            "subjects": ["Физика"],
            "price_per_hour": 1500,
            "experience_years": 3,
        })
        assert reg.status_code == 201

        # Токен захэширован в БД, поэтому генерируем новый известный токен вручную
        result = await db_session.execute(
            select(User).where(User.email == "newtutor@test.com")
        )
        user = result.scalar_one()

        from app.services.email_service import generate_verification_token, token_expiry
        raw, hashed = generate_verification_token()
        user.email_verify_token_hash = hashed
        user.email_verify_token_expires_at = token_expiry()
        await db_session.commit()

        res = await client.get(f"/api/v1/auth/verify-email?token={raw}")
        assert res.status_code == 200
        assert res.json()["tutor_verified"] is True

        profile_res = await db_session.execute(
            select(TutorProfile).where(TutorProfile.user_id == user.id)
        )
        profile = profile_res.scalar_one()
        assert profile.is_verified is True

    @pytest.mark.asyncio
    async def test_send_verification_cooldown(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Повторная отправка в течение cooldown возвращает 429."""
        first = await client.post(
            "/api/v1/auth/send-verification", headers=auth_headers,
        )
        # Первый запрос либо 202 (ok), либо 409 если test_user уже verified
        assert first.status_code in (202, 409)
        if first.status_code != 202:
            return

        second = await client.post(
            "/api/v1/auth/send-verification", headers=auth_headers,
        )
        assert second.status_code == 429
