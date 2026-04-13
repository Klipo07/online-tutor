"""Сервис репетиторов — бизнес-логика маркетплейса."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.tutor import TutorProfile
from app.models.review import Review


async def get_tutors(
    db: AsyncSession,
    subject: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    """Получить список репетиторов с фильтрами и пагинацией."""
    query = (
        select(TutorProfile)
        .options(joinedload(TutorProfile.user))
        .where(TutorProfile.is_verified == True)
    )

    # Фильтр по цене
    if min_price is not None:
        query = query.where(TutorProfile.price_per_hour >= min_price)
    if max_price is not None:
        query = query.where(TutorProfile.price_per_hour <= max_price)

    # Фильтр по рейтингу
    if min_rating is not None:
        query = query.where(TutorProfile.rating >= min_rating)

    query = query.order_by(TutorProfile.rating.desc())
    result = await db.execute(query)
    all_profiles = result.unique().scalars().all()

    # Фильтр по предмету — в Python, чтобы работало на любом SQL-диалекте
    if subject:
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
            "bio": profile.bio,
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
        "bio": profile.bio,
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
