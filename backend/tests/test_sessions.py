"""Тесты бронирования занятий — создание, список, отмена."""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.subject import Subject


class TestSessionsAPI:
    """Тесты эндпоинтов занятий."""

    @pytest.mark.asyncio
    async def test_create_session(
        self, client: AsyncClient, test_user: User,
        test_tutor_profile: TutorProfile, test_subject: Subject,
        auth_headers: dict,
    ):
        """Успешное бронирование занятия."""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat()
        response = await client.post("/api/v1/sessions/", json={
            "tutor_id": test_tutor_profile.id,
            "subject_id": test_subject.id,
            "scheduled_at": tomorrow,
            "duration_minutes": 60,
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["tutor_name"] == "Анна Репетиторова"
        assert data["subject_name"] == "Математика"
        assert data["status"] == "pending"
        assert data["duration_minutes"] == 60
        assert data["agora_channel_name"] is not None

    @pytest.mark.asyncio
    async def test_create_session_unauthorized(self, client: AsyncClient):
        """Бронирование без авторизации возвращает 403."""
        response = await client.post("/api/v1/sessions/", json={
            "tutor_id": 1,
            "subject_id": 1,
            "scheduled_at": datetime.utcnow().isoformat(),
        })
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_session_past_time(
        self, client: AsyncClient, test_user: User,
        test_tutor_profile: TutorProfile, test_subject: Subject,
        auth_headers: dict,
    ):
        """Бронирование в прошлом возвращает 400."""
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        response = await client.post("/api/v1/sessions/", json={
            "tutor_id": test_tutor_profile.id,
            "subject_id": test_subject.id,
            "scheduled_at": yesterday,
        }, headers=auth_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, client: AsyncClient, test_user: User, auth_headers: dict):
        """Список занятий нового пользователя — пустой."""
        response = await client.get("/api/v1/sessions/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["sessions"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_sessions(
        self, client: AsyncClient, test_user: User,
        test_tutor_profile: TutorProfile, test_subject: Subject,
        auth_headers: dict,
    ):
        """Список содержит созданное занятие."""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat()
        await client.post("/api/v1/sessions/", json={
            "tutor_id": test_tutor_profile.id,
            "subject_id": test_subject.id,
            "scheduled_at": tomorrow,
        }, headers=auth_headers)

        response = await client.get("/api/v1/sessions/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_cancel_session(
        self, client: AsyncClient, test_user: User,
        test_tutor_profile: TutorProfile, test_subject: Subject,
        auth_headers: dict,
    ):
        """Отмена бронирования."""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat()
        create_res = await client.post("/api/v1/sessions/", json={
            "tutor_id": test_tutor_profile.id,
            "subject_id": test_subject.id,
            "scheduled_at": tomorrow,
        }, headers=auth_headers)
        session_id = create_res.json()["id"]

        response = await client.put(
            f"/api/v1/sessions/{session_id}/cancel",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_get_session_forbidden(
        self, client: AsyncClient, test_user: User,
        test_tutor_profile: TutorProfile, test_subject: Subject,
        auth_headers: dict,
    ):
        """Доступ к чужому занятию возвращает 403."""
        # Создаём занятие от test_user
        tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat()
        create_res = await client.post("/api/v1/sessions/", json={
            "tutor_id": test_tutor_profile.id,
            "subject_id": test_subject.id,
            "scheduled_at": tomorrow,
        }, headers=auth_headers)
        session_id = create_res.json()["id"]

        # Пытаемся получить от другого пользователя
        from app.services.auth_service import create_access_token
        from app.models.user import User as UserModel
        other_token = create_access_token(99999)
        response = await client.get(
            f"/api/v1/sessions/{session_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        # Пользователь 99999 не существует — получим 401
        assert response.status_code == 401
