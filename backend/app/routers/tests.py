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

router = APIRouter()


class TestFeedbackRequest(BaseModel):
    """Фидбек после прохождения теста."""
    rating: FeedbackRating
    comment: str | None = Field(default=None, max_length=500)


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

    return [
        {
            "id": t.id,
            "subject_id": t.subject_id,
            "topic": t.topic,
            "exam_type": t.exam_type.value,
            "task_number": t.task_number,
            "difficulty": t.difficulty.value,
            "questions_count": len(t.questions) if isinstance(t.questions, list) else 0,
            "created_at": t.created_at.isoformat(),
        }
        for t in tests
    ]


@router.get("/task-numbers")
async def list_task_numbers(
    subject_id: int,
    exam_type: ExamType,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список доступных номеров заданий для предмета и формата."""
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
    return [{"task_number": n, "count": c} for n, c in result.all() if n is not None]


@router.get("/subjects-with-tests")
async def subjects_with_tests(
    exam_type: ExamType | None = None,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Предметы, по которым есть тесты (с подсчётом)."""
    query = (
        select(Subject.id, Subject.name, func.count(Test.id))
        .join(Test, Test.subject_id == Subject.id)
    )
    if exam_type is not None:
        query = query.where(Test.exam_type == exam_type)
    query = query.group_by(Subject.id, Subject.name).order_by(Subject.name)
    result = await db.execute(query)
    return [{"id": sid, "name": name, "tests_count": cnt} for sid, name, cnt in result.all()]


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

    # Вопросы — без поля correct (его проверяем на submit)
    questions = []
    for i, q in enumerate(test.questions or []):
        questions.append(
            {
                "id": i + 1,
                "question": q.get("question", ""),
                "options": q.get("options"),
                "type": q.get("type", "multiple_choice"),
            }
        )

    return {
        "id": test.id,
        "subject_id": test.subject_id,
        "topic": test.topic,
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
