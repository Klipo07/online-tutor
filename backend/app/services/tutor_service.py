"""Сервис репетиторов — бизнес-логика маркетплейса."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, cast, distinct
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.booking import BookingSession, BookingStatus
from app.models.subject import Subject
from app.models.tutor import TutorProfile
from app.models.review import Review
from app.models.user import User


async def get_tutors(
    db: AsyncSession,
    subject: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    """Получить список верифицированных репетиторов с фильтрами и пагинацией.

    Фильтр по предмету на PostgreSQL использует JSONB-оператор @> и GIN-индекс
    `ix_tutor_profiles_subjects_gin`; на SQLite (тесты) — Python-fallback.
    """
    query = (
        select(TutorProfile)
        .options(joinedload(TutorProfile.user))
        .where(TutorProfile.is_verified == True)
    )

    if min_price is not None:
        query = query.where(TutorProfile.price_per_hour >= min_price)
    if max_price is not None:
        query = query.where(TutorProfile.price_per_hour <= max_price)

    if min_rating is not None:
        query = query.where(TutorProfile.rating >= min_rating)

    # Фильтр по предмету — SQL на PostgreSQL, Python на SQLite
    dialect = db.bind.dialect.name if db.bind else ""
    use_jsonb = subject is not None and dialect == "postgresql"
    if use_jsonb:
        query = query.where(TutorProfile.subjects.cast(JSONB).contains([subject]))

    query = query.order_by(TutorProfile.rating.desc())
    result = await db.execute(query)
    all_profiles = result.unique().scalars().all()

    # Python-fallback для диалектов без JSONB (SQLite в тестах)
    if subject is not None and not use_jsonb:
        all_profiles = [p for p in all_profiles if subject in (p.subjects or [])]

    total = len(all_profiles)
    profiles = all_profiles[(page - 1) * per_page : page * per_page]

    # Формируем ответ с данными пользователя
    tutors = []
    for profile in profiles:
        tutors.append({
            "id": profile.id,
            "user_id": profile.user_id,
            "full_name": profile.user.full_name,
            "subjects": profile.subjects,
            "price_per_hour": float(profile.price_per_hour),
            "experience_years": profile.experience_years,
            "bio": profile.user.bio,
            "education": profile.education,
            "rating": float(profile.rating),
            "reviews_count": profile.reviews_count,
            "is_verified": profile.is_verified,
            "avatar_url": profile.user.avatar_url,
        })

    return tutors, total


async def get_tutor_by_id(db: AsyncSession, tutor_id: int) -> dict | None:
    """Получить профиль репетитора по ID."""
    query = (
        select(TutorProfile)
        .options(joinedload(TutorProfile.user))
        .where(TutorProfile.id == tutor_id)
    )
    result = await db.execute(query)
    profile = result.unique().scalar_one_or_none()

    if profile is None:
        return None

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": profile.user.full_name,
        "subjects": profile.subjects,
        "price_per_hour": float(profile.price_per_hour),
        "experience_years": profile.experience_years,
        "bio": profile.user.bio,
        "education": profile.education,
        "rating": float(profile.rating),
        "reviews_count": profile.reviews_count,
        "is_verified": profile.is_verified,
        "avatar_url": profile.user.avatar_url,
    }


async def create_review(
    db: AsyncSession,
    tutor_id: int,
    student_id: int,
    rating: int,
    comment: str,
) -> Review:
    """Создать отзыв и обновить рейтинг репетитора."""
    # Создаём отзыв
    review = Review(
        tutor_id=tutor_id,
        student_id=student_id,
        rating=rating,
        comment=comment,
    )
    db.add(review)

    # Пересчитываем средний рейтинг репетитора
    profile = await db.get(TutorProfile, tutor_id)
    if profile:
        avg_query = select(func.avg(Review.rating)).where(Review.tutor_id == tutor_id)
        count_query = select(func.count()).where(Review.tutor_id == tutor_id)

        avg_result = await db.execute(avg_query)
        count_result = await db.execute(count_query)

        new_rating = avg_result.scalar() or 0
        new_count = count_result.scalar() or 0

        # Учитываем текущий отзыв (ещё не закоммичен)
        total_rating = float(new_rating) * new_count + rating
        total_count = new_count + 1
        profile.rating = round(total_rating / total_count, 2)
        profile.reviews_count = total_count

    await db.commit()
    await db.refresh(review)
    return review


async def get_tutor_stats(db: AsyncSession, tutor_profile_id: int) -> dict:
    """Посчитать агрегированную статистику для дашборда репетитора.

    - students_count — уникальные ученики за всё время (по завершённым и предстоящим)
    - sessions_completed — проведённые занятия (status=completed)
    - sessions_upcoming — активные брони в будущем
    - earnings_month — суммарный price проведённых за последние 30 дней
    - rating / reviews_count — из TutorProfile (кэшируются при создании отзыва)
    - next_session_* — ближайшее предстоящее занятие
    """
    profile = await db.get(TutorProfile, tutor_profile_id)
    if profile is None:
        raise ValueError("Профиль репетитора не найден")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    month_ago = now - timedelta(days=30)

    # Кол-во уникальных учеников (по всем не отменённым бронированиям)
    students_q = select(func.count(distinct(BookingSession.student_id))).where(
        BookingSession.tutor_id == tutor_profile_id,
        BookingSession.status != BookingStatus.cancelled,
    )
    students_count = (await db.execute(students_q)).scalar() or 0

    # Проведённые занятия
    completed_q = select(func.count()).where(
        BookingSession.tutor_id == tutor_profile_id,
        BookingSession.status == BookingStatus.completed,
    )
    sessions_completed = (await db.execute(completed_q)).scalar() or 0

    # Предстоящие
    upcoming_q = select(func.count()).where(
        BookingSession.tutor_id == tutor_profile_id,
        BookingSession.status.in_([BookingStatus.pending, BookingStatus.confirmed]),
        BookingSession.scheduled_at >= now,
    )
    sessions_upcoming = (await db.execute(upcoming_q)).scalar() or 0

    # Заработок за месяц (по завершённым + активным в окне 30 дней)
    earn_q = select(func.coalesce(func.sum(BookingSession.price), 0)).where(
        BookingSession.tutor_id == tutor_profile_id,
        BookingSession.status.in_([BookingStatus.completed, BookingStatus.confirmed]),
        BookingSession.scheduled_at >= month_ago,
        BookingSession.scheduled_at < now,
    )
    earnings_month = float((await db.execute(earn_q)).scalar() or 0)

    # Ближайшее занятие
    next_q = (
        select(BookingSession)
        .options(
            joinedload(BookingSession.student),
            joinedload(BookingSession.subject),
        )
        .where(
            BookingSession.tutor_id == tutor_profile_id,
            BookingSession.status.in_([BookingStatus.pending, BookingStatus.confirmed]),
            BookingSession.scheduled_at >= now,
        )
        .order_by(BookingSession.scheduled_at.asc())
        .limit(1)
    )
    next_booking = (await db.execute(next_q)).unique().scalar_one_or_none()

    return {
        "students_count": int(students_count),
        "sessions_completed": int(sessions_completed),
        "sessions_upcoming": int(sessions_upcoming),
        "earnings_month": round(earnings_month, 2),
        "rating": float(profile.rating),
        "reviews_count": profile.reviews_count,
        "next_session_at": next_booking.scheduled_at if next_booking else None,
        "next_session_student": next_booking.student.full_name if next_booking else None,
        "next_session_subject": next_booking.subject.name if next_booking else None,
    }


async def get_reviews(db: AsyncSession, tutor_id: int) -> list[dict]:
    """Получить все отзывы репетитора."""
    query = (
        select(Review)
        .options(joinedload(Review.student))
        .where(Review.tutor_id == tutor_id)
        .order_by(Review.created_at.desc())
    )
    result = await db.execute(query)
    reviews = result.unique().scalars().all()

    return [
        {
            "id": r.id,
            "tutor_id": r.tutor_id,
            "student_id": r.student_id,
            "student_name": r.student.full_name,
            "rating": r.rating,
            "comment": r.comment,
        }
        for r in reviews
    ]
