"""Роутер тестов — банк заданий ОГЭ/ЕГЭ с фильтрами."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.subject import Subject
from app.models.test import Difficulty, ExamType, Test, TestFeedback, FeedbackRating
from app.models.user import User
from app.services import cache
from app.services.math_format import format_questions, latex_to_unicode

router = APIRouter()

# Справочники теста меняются редко (только при добавлении новых задач в банк)
TESTS_META_TTL = 600


class TestRecommendRequest(BaseModel):
    """Запрос на адаптивный подбор тестов."""
    subject_id: int
    exam_type: ExamType
    task_number: int | None = None
    limit: int = Field(5, ge=1, le=20)


async def _pick_difficulty_for_user(
    db: AsyncSession, user_id: int, subject_id: int
) -> Difficulty:
    """Подобрать стартовую сложность на основе последних фидбеков пользователя.

    Смотрим последние 10 оценок по данному предмету. Правило:
    - >=60% too_easy  → hard
    - >=60% too_hard  → easy
    - иначе           → medium
    Если фидбеков нет — medium (нейтральный старт).
    """
    q = (
        select(TestFeedback.rating)
        .join(Test, Test.id == TestFeedback.test_id)
        .where(TestFeedback.user_id == user_id, Test.subject_id == subject_id)
        .order_by(TestFeedback.created_at.desc())
        .limit(10)
    )
    result = await db.execute(q)
    ratings = [r[0] for r in result.all()]
    if not ratings:
        return Difficulty.medium

    total = len(ratings)
    too_easy = sum(1 for r in ratings if r == FeedbackRating.too_easy)
    too_hard = sum(1 for r in ratings if r == FeedbackRating.too_hard)

    if too_easy / total >= 0.6:
        return Difficulty.hard
    if too_hard / total >= 0.6:
        return Difficulty.easy
    return Difficulty.medium


class TestFeedbackRequest(BaseModel):
    """Фидбек после прохождения теста."""
    rating: FeedbackRating
    comment: str | None = Field(default=None, max_length=500)


def _test_to_list_item(t: Test) -> dict:
    """Форматируем тест для списка — topic с конвертацией формул."""
    return {
        "id": t.id,
        "subject_id": t.subject_id,
        "topic": latex_to_unicode(t.topic),
        "exam_type": t.exam_type.value,
        "task_number": t.task_number,
        "difficulty": t.difficulty.value,
        "questions_count": len(t.questions) if isinstance(t.questions, list) else 0,
        "created_at": t.created_at.isoformat(),
    }


@router.get("")
async def list_tests(
    subject_id: int | None = None,
    exam_type: ExamType | None = None,
    task_number: int | None = None,
    difficulty: Difficulty | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список тестов с фильтрами."""
    query = select(Test)
    if subject_id is not None:
        query = query.where(Test.subject_id == subject_id)
    if exam_type is not None:
        query = query.where(Test.exam_type == exam_type)
    if task_number is not None:
        query = query.where(Test.task_number == task_number)
    if difficulty is not None:
        query = query.where(Test.difficulty == difficulty)

    query = query.order_by(Test.id.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    tests = result.scalars().all()

    return [_test_to_list_item(t) for t in tests]


@router.post("/recommend")
async def recommend_tests(
    data: TestRecommendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Адаптивный подбор тестов под пользователя.

    Смотрим фидбеки (слишком легко / в самый раз / слишком сложно) по предмету,
    подбираем сложность и случайные тесты из банка. Если под подобранную сложность
    тестов нет — откатываемся к medium, потом к any.
    """
    picked = await _pick_difficulty_for_user(db, current_user.id, data.subject_id)

    async def _fetch(diff: Difficulty | None) -> list[Test]:
        q = select(Test).where(
            Test.subject_id == data.subject_id,
            Test.exam_type == data.exam_type,
        )
        if data.task_number is not None:
            q = q.where(Test.task_number == data.task_number)
        if diff is not None:
            q = q.where(Test.difficulty == diff)
        # func.random() работает на PostgreSQL и SQLite (random() alias)
        q = q.order_by(func.random()).limit(data.limit)
        res = await db.execute(q)
        return list(res.scalars().all())

    tests = await _fetch(picked)
    fallback_used = False
    if not tests and picked != Difficulty.medium:
        tests = await _fetch(Difficulty.medium)
        fallback_used = True
    if not tests:
        tests = await _fetch(None)
        fallback_used = True

    return {
        "difficulty": picked.value,
        "fallback_used": fallback_used,
        "tests": [_test_to_list_item(t) for t in tests],
    }


@router.get("/task-numbers")
async def list_task_numbers(
    subject_id: int,
    exam_type: ExamType,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список доступных номеров заданий для предмета и формата."""
    cache_key = f"tests:task-numbers:{subject_id}:{exam_type.value}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    query = (
        select(Test.task_number, func.count())
        .where(
            Test.subject_id == subject_id,
            Test.exam_type == exam_type,
            Test.task_number.is_not(None),
        )
        .group_by(Test.task_number)
        .order_by(Test.task_number)
    )
    result = await db.execute(query)
    payload = [{"task_number": n, "count": c} for n, c in result.all() if n is not None]
    await cache.set(cache_key, payload, ttl=TESTS_META_TTL)
    return payload


@router.get("/subjects-with-tests")
async def subjects_with_tests(
    exam_type: ExamType | None = None,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Предметы, по которым есть тесты (с подсчётом)."""
    cache_key = f"tests:subjects-with-tests:{exam_type.value if exam_type else 'all'}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    query = (
        select(Subject.id, Subject.name, func.count(Test.id))
        .join(Test, Test.subject_id == Subject.id)
    )
    if exam_type is not None:
        query = query.where(Test.exam_type == exam_type)
    query = query.group_by(Subject.id, Subject.name).order_by(Subject.name)
    result = await db.execute(query)
    payload = [{"id": sid, "name": name, "tests_count": cnt} for sid, name, cnt in result.all()]
    await cache.set(cache_key, payload, ttl=TESTS_META_TTL)
    return payload


@router.get("/{test_id}")
async def get_test(
    test_id: int,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить тест с вопросами (без правильных ответов)."""
    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")

    # Вопросы — без поля correct (его проверяем на submit).
    # Прогоняем через format_questions: LaTeX-маркеры → unicode (² √ π и т.п.)
    raw_questions = []
    for i, q in enumerate(test.questions or []):
        raw_questions.append(
            {
                "id": i + 1,
                "question": q.get("question", ""),
                "options": q.get("options"),
                "type": q.get("type", "multiple_choice"),
            }
        )
    questions = format_questions(raw_questions)

    return {
        "id": test.id,
        "subject_id": test.subject_id,
        "topic": latex_to_unicode(test.topic),
        "exam_type": test.exam_type.value,
        "task_number": test.task_number,
        "difficulty": test.difficulty.value,
        "questions": questions,
    }


@router.post("/{test_id}/feedback", status_code=201)
async def submit_feedback(
    test_id: int,
    data: TestFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Оставить фидбек по тесту — лёгкий/нормальный/сложный.

    Используется для сбора сигналов об оценке сложности и будущей автокоррекции.
    """
    # Проверяем существование теста
    exists = await db.execute(select(Test.id).where(Test.id == test_id))
    if exists.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Тест не найден")

    feedback = TestFeedback(
        user_id=current_user.id,
        test_id=test_id,
        rating=data.rating,
        comment=(data.comment or "").strip() or None,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return {
        "id": feedback.id,
        "test_id": feedback.test_id,
        "rating": feedback.rating.value,
        "created_at": feedback.created_at.isoformat(),
    }
