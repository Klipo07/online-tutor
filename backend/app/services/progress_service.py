"""Сервис прогресса и аналитики — обновление, статистика, рекомендации."""

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.progress import StudentProgress
from app.models.test import Test, TestAttempt
from app.models.chat import ChatSession
from app.models.booking import BookingSession, BookingStatus
from app.models.subject import Subject


async def update_progress_after_test(
    db: AsyncSession,
    user_id: int,
    test: Test,
    score: int,
) -> StudentProgress:
    """Обновить прогресс ученика после прохождения теста."""
    # Ищем существующую запись прогресса по предмету
    query = select(StudentProgress).where(
        StudentProgress.user_id == user_id,
        StudentProgress.subject_id == test.subject_id,
    )
    result = await db.execute(query)
    progress = result.scalar_one_or_none()

    if progress is None:
        # Создаём новую запись прогресса
        progress = StudentProgress(
            user_id=user_id,
            subject_id=test.subject_id,
            score=score,
            weak_topics=[],
            last_activity=datetime.utcnow(),
        )
        db.add(progress)
    else:
        # Пересчитываем средний балл на основе всех попыток
        avg_query = select(func.avg(TestAttempt.score)).join(Test).where(
            TestAttempt.user_id == user_id,
            Test.subject_id == test.subject_id,
        )
        avg_result = await db.execute(avg_query)
        avg_score = avg_result.scalar() or score
        progress.score = round(float(avg_score))
        progress.last_activity = datetime.utcnow()

    # Определяем слабые темы (тесты с баллом < 60)
    weak_query = (
        select(Test.topic, func.avg(TestAttempt.score))
        .join(Test)
        .where(
            TestAttempt.user_id == user_id,
            Test.subject_id == test.subject_id,
        )
        .group_by(Test.topic)
        .having(func.avg(TestAttempt.score) < 60)
    )
    weak_result = await db.execute(weak_query)
    progress.weak_topics = [row[0] for row in weak_result.all()]

    await db.commit()
    await db.refresh(progress)
    return progress


async def get_user_stats(db: AsyncSession, user_id: int) -> dict:
    """Получить общую статистику пользователя."""
    # Количество пройденных тестов
    tests_count_query = select(func.count()).where(TestAttempt.user_id == user_id)
    tests_result = await db.execute(tests_count_query)
    tests_count = tests_result.scalar() or 0

    # Средний балл по всем тестам
    avg_score_query = select(func.avg(TestAttempt.score)).where(
        TestAttempt.user_id == user_id
    )
    avg_result = await db.execute(avg_score_query)
    avg_score = round(float(avg_result.scalar() or 0))

    # Количество сессий чата
    chats_query = select(func.count()).where(ChatSession.user_id == user_id)
    chats_result = await db.execute(chats_query)
    chats_count = chats_result.scalar() or 0

    # Количество занятий с репетиторами
    bookings_query = select(func.count()).where(
        BookingSession.student_id == user_id,
        BookingSession.status == BookingStatus.completed,
    )
    bookings_result = await db.execute(bookings_query)
    bookings_count = bookings_result.scalar() or 0

    # Количество изученных предметов
    subjects_query = select(func.count(func.distinct(StudentProgress.subject_id))).where(
        StudentProgress.user_id == user_id
    )
    subjects_result = await db.execute(subjects_query)
    subjects_count = subjects_result.scalar() or 0

    # Общее время на тесты (секунды)
    time_query = select(func.sum(TestAttempt.time_spent_seconds)).where(
        TestAttempt.user_id == user_id
    )
    time_result = await db.execute(time_query)
    total_time = time_result.scalar() or 0

    return {
        "tests_completed": tests_count,
        "average_score": avg_score,
        "chat_sessions": chats_count,
        "lessons_completed": bookings_count,
        "subjects_studied": subjects_count,
        "total_study_time_minutes": round(total_time / 60) if total_time else 0,
    }


async def get_recommendations(db: AsyncSession, user_id: int) -> list[dict]:
    """Персональные рекомендации на основе прогресса и истории."""
    recommendations = []

    # Получаем прогресс по предметам
    progress_query = (
        select(StudentProgress)
        .options(joinedload(StudentProgress.subject))
        .where(StudentProgress.user_id == user_id)
        .order_by(StudentProgress.score.asc())
    )
    progress_result = await db.execute(progress_query)
    progress_records = progress_result.unique().scalars().all()

    # Рекомендации по слабым предметам (балл < 60)
    for record in progress_records:
        if record.score < 60:
            recommendations.append({
                "type": "weak_subject",
                "priority": "high",
                "subject": record.subject.name,
                "score": record.score,
                "message": f"Подтяните {record.subject.name} — текущий балл {record.score}%",
                "action": "Пройдите тест или задайте вопросы AI-тьютору",
            })

    # Рекомендации по слабым темам
    for record in progress_records:
        for topic in (record.weak_topics or []):
            recommendations.append({
                "type": "weak_topic",
                "priority": "medium",
                "subject": record.subject.name,
                "topic": topic,
                "message": f"Повторите тему «{topic}» по предмету {record.subject.name}",
                "action": "Пройдите тест по этой теме",
            })

    # Если нет тестов вообще — рекомендуем начать
    tests_query = select(func.count()).where(TestAttempt.user_id == user_id)
    tests_result = await db.execute(tests_query)
    if (tests_result.scalar() or 0) == 0:
        recommendations.append({
            "type": "start",
            "priority": "high",
            "message": "Пройдите первый тест, чтобы оценить уровень знаний",
            "action": "Перейдите в раздел Тесты",
        })

    # Если мало чат-сессий — рекомендуем использовать AI
    chats_query = select(func.count()).where(ChatSession.user_id == user_id)
    chats_result = await db.execute(chats_query)
    if (chats_result.scalar() or 0) < 3:
        recommendations.append({
            "type": "use_ai",
            "priority": "low",
            "message": "Используйте AI-тьютора для разбора сложных тем",
            "action": "Задайте вопрос в AI-чате",
        })

    # Сортируем по приоритету
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda r: priority_order.get(r["priority"], 2))

    return recommendations


async def get_test_history(
    db: AsyncSession,
    user_id: int,
    limit: int = 20,
) -> list[dict]:
    """История прохождения тестов."""
    query = (
        select(TestAttempt)
        .options(joinedload(TestAttempt.test))
        .where(TestAttempt.user_id == user_id)
        .order_by(TestAttempt.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    attempts = result.unique().scalars().all()

    return [
        {
            "id": a.id,
            "test_id": a.test_id,
            "topic": a.test.topic,
            "difficulty": a.test.difficulty.value,
            "score": a.score,
            "time_spent_seconds": a.time_spent_seconds,
            "created_at": a.created_at.isoformat(),
        }
        for a in attempts
    ]
