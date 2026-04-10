"""Тесты маркетплейса репетиторов — список, профиль, отзывы."""

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.tutor import TutorProfile


class TestTutorsAPI:
    """Тесты эндпоинтов репетиторов."""

    @pytest.mark.asyncio
    async def test_list_tutors_empty(self, client: AsyncClient):
        """Пустой список репетиторов."""
        response = await client.get("/api/v1/tutors/")
        assert response.status_code == 200
        data = response.json()
        assert data["tutors"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_tutors(self, client: AsyncClient, test_tutor_profile: TutorProfile):
        """Список содержит верифицированного репетитора."""
        response = await client.get("/api/v1/tutors/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["tutors"][0]["full_name"] == "Анна Репетиторова"
        assert "Математика" in data["tutors"][0]["subjects"]

    @pytest.mark.asyncio
    async def test_list_tutors_filter_subject(self, client: AsyncClient, test_tutor_profile: TutorProfile):
        """Фильтр по предмету — Математика найдёт репетитора."""
        response = await client.get("/api/v1/tutors/?subject=Математика")
        assert response.status_code == 200
        assert response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_list_tutors_filter_wrong_subject(self, client: AsyncClient, test_tutor_profile: TutorProfile):
        """Фильтр по несуществующему предмету — пусто."""
        response = await client.get("/api/v1/tutors/?subject=Астрономия")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_get_tutor_profile(self, client: AsyncClient, test_tutor_profile: TutorProfile):
        """Получение профиля репетитора по ID."""
        response = await client.get(f"/api/v1/tutors/{test_tutor_profile.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Анна Репетиторова"
        assert data["price_per_hour"] == 1500
        assert data["experience_years"] == 8

    @pytest.mark.asyncio
    async def test_get_tutor_not_found(self, client: AsyncClient):
        """Несуществующий репетитор возвращает 404."""
        response = await client.get("/api/v1/tutors/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_review(
        self, client: AsyncClient, test_user: User,
        test_tutor_profile: TutorProfile, auth_headers: dict,
    ):
        """Создание отзыва о репетиторе."""
        response = await client.post(
            f"/api/v1/tutors/{test_tutor_profile.id}/review",
            json={"rating": 5, "comment": "Отличный преподаватель, объясняет понятно!"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["student_name"] == "Иван Тестов"

    @pytest.mark.asyncio
    async def test_create_review_unauthorized(self, client: AsyncClient, test_tutor_profile: TutorProfile):
        """Отзыв без авторизации возвращает 403."""
        response = await client.post(
            f"/api/v1/tutors/{test_tutor_profile.id}/review",
            json={"rating": 5, "comment": "Тестовый отзыв"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_review_self(
        self, client: AsyncClient, test_tutor_user: User,
        test_tutor_profile: TutorProfile, tutor_auth_headers: dict,
    ):
        """Нельзя оставить отзыв самому себе."""
        response = await client.post(
            f"/api/v1/tutors/{test_tutor_profile.id}/review",
            json={"rating": 5, "comment": "Сам себя хвалю"},
            headers=tutor_auth_headers,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_reviews(
        self, client: AsyncClient, test_user: User,
        test_tutor_profile: TutorProfile, auth_headers: dict,
    ):
        """Получение списка отзывов."""
        # Создаём отзыв
        await client.post(
            f"/api/v1/tutors/{test_tutor_profile.id}/review",
            json={"rating": 4, "comment": "Хороший репетитор"},
            headers=auth_headers,
        )

        response = await client.get(f"/api/v1/tutors/{test_tutor_profile.id}/reviews")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["rating"] == 4
