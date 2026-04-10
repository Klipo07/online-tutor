"""Тесты предметов и тем."""

import pytest
from httpx import AsyncClient

from app.models.subject import Subject


class TestSubjectsAPI:
    """Тесты эндпоинтов предметов."""

    @pytest.mark.asyncio
    async def test_list_subjects_empty(self, client: AsyncClient):
        """Пустой список предметов."""
        response = await client.get("/api/v1/subjects/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_subjects(self, client: AsyncClient, test_subject: Subject):
        """Список предметов содержит созданный предмет."""
        response = await client.get("/api/v1/subjects/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Математика"
        assert data[0]["slug"] == "math"

    @pytest.mark.asyncio
    async def test_get_subject_with_topics(self, client: AsyncClient, test_subject: Subject):
        """Получение предмета с темами."""
        response = await client.get(f"/api/v1/subjects/{test_subject.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Математика"
        assert len(data["topics"]) == 3
        assert data["topics"][0]["name"] == "Квадратные уравнения"

    @pytest.mark.asyncio
    async def test_get_subject_not_found(self, client: AsyncClient):
        """Несуществующий предмет возвращает 404."""
        response = await client.get("/api/v1/subjects/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_topics(self, client: AsyncClient, test_subject: Subject):
        """Получение тем по предмету."""
        response = await client.get(f"/api/v1/subjects/{test_subject.id}/topics")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Проверяем порядок
        assert data[0]["order"] == 1
        assert data[1]["order"] == 2

    @pytest.mark.asyncio
    async def test_get_topics_not_found(self, client: AsyncClient):
        """Темы несуществующего предмета возвращают 404."""
        response = await client.get("/api/v1/subjects/99999/topics")
        assert response.status_code == 404
