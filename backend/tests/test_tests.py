"""Тесты эндпоинтов банка тестов: список, адаптивный подбор /tests/recommend."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject
from app.models.test import Difficulty, ExamType, FeedbackRating, Test, TestFeedback
from app.models.user import User


def _make_test(
    subject_id: int,
    *,
    topic: str = "Тема",
    exam_type: ExamType = ExamType.ege,
    task_number: int | None = 1,
    difficulty: Difficulty = Difficulty.medium,
) -> Test:
    """Фабрика теста для банка — с одним тривиальным вопросом."""
    return Test(
        subject_id=subject_id,
        topic=topic,
        exam_type=exam_type,
        task_number=task_number,
        difficulty=difficulty,
        questions=[{"question": "2+2?", "options": ["3", "4"], "correct": "4"}],
        created_by_ai=False,
    )


async def _seed_tests_for_subject(
    db: AsyncSession, subject_id: int, difficulties: list[Difficulty]
) -> list[Test]:
    """Создать N тестов указанных сложностей для предмета (ЕГЭ, задача 1)."""
    tests = [_make_test(subject_id, difficulty=d, topic=f"T-{d.value}") for d in difficulties]
    db.add_all(tests)
    await db.commit()
    for t in tests:
        await db.refresh(t)
    return tests


async def _feedback(
    db: AsyncSession, user_id: int, test_id: int, rating: FeedbackRating
) -> None:
    """Записать фидбек пользователя по тесту."""
    db.add(TestFeedback(user_id=user_id, test_id=test_id, rating=rating))
    await db.commit()


class TestRecommendEndpoint:
    """Адаптивный подбор /tests/recommend."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient, test_subject: Subject):
        """Без токена — 401 (HTTPBearer)."""
        response = await client.post(
            "/api/v1/tests/recommend",
            json={"subject_id": test_subject.id, "exam_type": "ege"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_no_feedbacks_returns_medium(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_subject: Subject,
        auth_headers: dict,
    ):
        """Новый пользователь без фидбеков → подбираем medium."""
        await _seed_tests_for_subject(
            db_session,
            test_subject.id,
            [Difficulty.easy, Difficulty.medium, Difficulty.medium, Difficulty.hard],
        )

        response = await client.post(
            "/api/v1/tests/recommend",
            headers=auth_headers,
            json={"subject_id": test_subject.id, "exam_type": "ege", "limit": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["difficulty"] == "medium"
        # Все возвращённые тесты — medium
        assert len(data["tests"]) > 0
        assert all(t["difficulty"] == "medium" for t in data["tests"])
        assert data["fallback_used"] is False

    @pytest.mark.asyncio
    async def test_too_easy_feedback_bumps_to_hard(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_subject: Subject,
        auth_headers: dict,
    ):
        """Много 'too_easy' в фидбеках → подбираем hard."""
        tests = await _seed_tests_for_subject(
            db_session,
            test_subject.id,
            [Difficulty.easy, Difficulty.medium, Difficulty.hard, Difficulty.hard],
        )
        # 3 из 3 — слишком легко (>60% порог)
        for t in tests[:3]:
            await _feedback(db_session, test_user.id, t.id, FeedbackRating.too_easy)

        response = await client.post(
            "/api/v1/tests/recommend",
            headers=auth_headers,
            json={"subject_id": test_subject.id, "exam_type": "ege"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["difficulty"] == "hard"
        assert all(t["difficulty"] == "hard" for t in data["tests"])

    @pytest.mark.asyncio
    async def test_too_hard_feedback_drops_to_easy(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_subject: Subject,
        auth_headers: dict,
    ):
        """Много 'too_hard' в фидбеках → подбираем easy."""
        tests = await _seed_tests_for_subject(
            db_session,
            test_subject.id,
            [Difficulty.easy, Difficulty.easy, Difficulty.medium, Difficulty.hard],
        )
        for t in tests[:3]:
            await _feedback(db_session, test_user.id, t.id, FeedbackRating.too_hard)

        response = await client.post(
            "/api/v1/tests/recommend",
            headers=auth_headers,
            json={"subject_id": test_subject.id, "exam_type": "ege"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["difficulty"] == "easy"
        assert all(t["difficulty"] == "easy" for t in data["tests"])

    @pytest.mark.asyncio
    async def test_mixed_feedback_stays_medium(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_subject: Subject,
        auth_headers: dict,
    ):
        """Смешанные фидбеки (ни один рейтинг не >=60%) → остаёмся на medium."""
        tests = await _seed_tests_for_subject(
            db_session,
            test_subject.id,
            [Difficulty.medium, Difficulty.medium, Difficulty.medium],
        )
        # 1 too_easy, 1 ok, 1 too_hard — ни один не доминирует
        await _feedback(db_session, test_user.id, tests[0].id, FeedbackRating.too_easy)
        await _feedback(db_session, test_user.id, tests[1].id, FeedbackRating.ok)
        await _feedback(db_session, test_user.id, tests[2].id, FeedbackRating.too_hard)

        response = await client.post(
            "/api/v1/tests/recommend",
            headers=auth_headers,
            json={"subject_id": test_subject.id, "exam_type": "ege"},
        )
        assert response.status_code == 200
        assert response.json()["difficulty"] == "medium"

    @pytest.mark.asyncio
    async def test_fallback_when_no_tests_at_picked_difficulty(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_subject: Subject,
        auth_headers: dict,
    ):
        """Подобрали hard, но hard-тестов нет → откат на medium, fallback_used=True."""
        # В банке есть только easy и medium
        tests = await _seed_tests_for_subject(
            db_session,
            test_subject.id,
            [Difficulty.easy, Difficulty.medium, Difficulty.medium],
        )
        # 3 too_easy → алгоритм хочет hard
        for t in tests:
            await _feedback(db_session, test_user.id, t.id, FeedbackRating.too_easy)

        response = await client.post(
            "/api/v1/tests/recommend",
            headers=auth_headers,
            json={"subject_id": test_subject.id, "exam_type": "ege"},
        )
        assert response.status_code == 200
        data = response.json()
        # picked — hard (его запросили по правилу), но отдали medium
        assert data["difficulty"] == "hard"
        assert data["fallback_used"] is True
        assert len(data["tests"]) > 0
        # Fallback хоть и medium, но главное — тесты отдали
        assert all(t["difficulty"] in ("medium", "easy") for t in data["tests"])

    @pytest.mark.asyncio
    async def test_filter_by_task_number(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_subject: Subject,
        auth_headers: dict,
    ):
        """Фильтр по task_number применяется — возвращаем только задания с указанным номером."""
        db_session.add_all([
            _make_test(test_subject.id, task_number=1, difficulty=Difficulty.medium),
            _make_test(test_subject.id, task_number=2, difficulty=Difficulty.medium),
            _make_test(test_subject.id, task_number=3, difficulty=Difficulty.medium),
        ])
        await db_session.commit()

        response = await client.post(
            "/api/v1/tests/recommend",
            headers=auth_headers,
            json={
                "subject_id": test_subject.id,
                "exam_type": "ege",
                "task_number": 2,
                "limit": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["tests"]) == 1
        assert data["tests"][0]["task_number"] == 2

    @pytest.mark.asyncio
    async def test_feedback_from_other_subject_ignored(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_subject: Subject,
        auth_headers: dict,
    ):
        """Фидбеки по другому предмету не влияют на подбор сложности."""
        # Второй предмет — физика
        physics = Subject(name="Физика", slug="physics")
        db_session.add(physics)
        await db_session.commit()
        await db_session.refresh(physics)

        # В физике — 3 too_easy (не должны повлиять на математику)
        phys_tests = await _seed_tests_for_subject(
            db_session, physics.id, [Difficulty.easy, Difficulty.medium, Difficulty.hard]
        )
        for t in phys_tests:
            await _feedback(db_session, test_user.id, t.id, FeedbackRating.too_easy)

        # В математике — ни одного фидбека, только medium-тесты
        await _seed_tests_for_subject(db_session, test_subject.id, [Difficulty.medium])

        response = await client.post(
            "/api/v1/tests/recommend",
            headers=auth_headers,
            json={"subject_id": test_subject.id, "exam_type": "ege"},
        )
        assert response.status_code == 200
        # По математике — без фидбеков → medium (фидбеки физики не смешиваются)
        assert response.json()["difficulty"] == "medium"


class TestListTestsLatexFormatting:
    """Регрессия: /tests/{id} конвертирует LaTeX в тексте и опциях."""

    @pytest.mark.asyncio
    async def test_get_test_converts_latex(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_subject: Subject,
        auth_headers: dict,
    ):
        """Вопрос с $x^2$ должен вернуться с x² в ответе."""
        t = Test(
            subject_id=test_subject.id,
            topic=r"Уравнение $x^2$",
            exam_type=ExamType.ege,
            task_number=1,
            difficulty=Difficulty.medium,
            questions=[
                {
                    "question": r"Найдите $\sqrt{9}$",
                    "options": [r"$\pi$", "3"],
                    "correct": "3",
                }
            ],
            created_by_ai=False,
        )
        db_session.add(t)
        await db_session.commit()
        await db_session.refresh(t)

        response = await client.get(f"/api/v1/tests/{t.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == "Уравнение x²"
        assert data["questions"][0]["question"] == "Найдите √9"
        assert data["questions"][0]["options"] == ["π", "3"]
