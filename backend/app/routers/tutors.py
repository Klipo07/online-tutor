"""Роутер репетиторов — список, профиль, отзывы, приватные /me/* эндпоинты."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.tutor import DEFAULT_WORKING_HOURS, TutorProfile
from app.models.user import User, UserRole
from app.schemas.tutor import (
    TutorResponse,
    TutorListResponse,
    ReviewCreate,
    ReviewResponse,
    TutorProfileUpdate,
    TutorScheduleResponse,
    TutorScheduleUpdate,
    TutorStatsResponse,
)
from app.services.tutor_service import (
    get_tutors,
    get_tutor_by_id,
    create_review,
    get_reviews,
    get_tutor_stats,
)
from app.services.session_service import get_tutor_slots

router = APIRouter()


async def _get_my_tutor_profile(
    current_user: User, db: AsyncSession
) -> TutorProfile:
    """Вернуть профиль текущего пользователя-репетитора или 403."""
    if current_user.role != UserRole.tutor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступно только репетиторам",
        )
    result = await db.execute(
        select(TutorProfile).where(TutorProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль репетитора не найден",
        )
    return profile


@router.get("/", response_model=TutorListResponse)
async def list_tutors(
    subject: str | None = Query(None, description="Фильтр по предмету"),
    min_price: float | None = Query(None, ge=0, description="Минимальная цена"),
    max_price: float | None = Query(None, ge=0, description="Максимальная цена"),
    min_rating: float | None = Query(None, ge=0, le=5, description="Минимальный рейтинг"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=50, description="Количество на странице"),
    db: AsyncSession = Depends(get_db),
):
    """Список репетиторов с фильтрами и пагинацией."""
    tutors, total = await get_tutors(
        db, subject=subject, min_price=min_price,
        max_price=max_price, min_rating=min_rating,
        page=page, per_page=per_page,
    )
    return TutorListResponse(
        tutors=tutors, total=total, page=page, per_page=per_page,
    )


# === Приватные /me/* эндпоинты репетитора ===
# Регистрируем ДО /{tutor_id}, иначе "me" будет трактоваться как ID

@router.get("/me/schedule", response_model=TutorScheduleResponse)
async def get_my_schedule(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить рабочие часы текущего репетитора."""
    profile = await _get_my_tutor_profile(current_user, db)
    return profile.working_hours or DEFAULT_WORKING_HOURS


@router.put("/me/schedule", response_model=TutorScheduleResponse)
async def update_my_schedule(
    data: TutorScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить рабочие часы — передаются все 7 дней сразу."""
    profile = await _get_my_tutor_profile(current_user, db)
    # Пересобираем словарь, чтобы заменить, а не мутировать вложенный JSON
    profile.working_hours = {
        "mon": data.mon,
        "tue": data.tue,
        "wed": data.wed,
        "thu": data.thu,
        "fri": data.fri,
        "sat": data.sat,
        "sun": data.sun,
    }
    await db.commit()
    await db.refresh(profile)
    return profile.working_hours


@router.patch("/me/profile", response_model=TutorResponse)
async def update_my_tutor_profile(
    data: TutorProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить tutor-специфичные поля: предметы, цена, опыт, образование."""
    profile = await _get_my_tutor_profile(current_user, db)
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет данных для обновления",
        )
    for field, value in update_data.items():
        setattr(profile, field, value)
    await db.commit()

    # Возвращаем в формате TutorResponse — через сервис, с join на user
    tutor = await get_tutor_by_id(db, profile.id)
    return tutor


@router.get("/me/stats", response_model=TutorStatsResponse)
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Статистика для дашборда репетитора — ученики, занятия, заработок."""
    profile = await _get_my_tutor_profile(current_user, db)
    stats = await get_tutor_stats(db, profile.id)
    return stats


@router.get("/me/reviews", response_model=list[ReviewResponse])
async def get_my_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отзывы о текущем репетиторе."""
    profile = await _get_my_tutor_profile(current_user, db)
    return await get_reviews(db, profile.id)


@router.get("/{tutor_id}", response_model=TutorResponse)
async def get_tutor(tutor_id: int, db: AsyncSession = Depends(get_db)):
    """Профиль репетитора по ID."""
    tutor = await get_tutor_by_id(db, tutor_id)
    if tutor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Репетитор не найден",
        )
    return tutor


@router.post("/{tutor_id}/review", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def add_review(
    tutor_id: int,
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Оставить отзыв о репетиторе (требует авторизации)."""
    # Проверяем что репетитор существует
    tutor = await get_tutor_by_id(db, tutor_id)
    if tutor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Репетитор не найден",
        )

    # Нельзя оставить отзыв самому себе
    if tutor["user_id"] == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя оставить отзыв самому себе",
        )

    review = await create_review(
        db, tutor_id=tutor_id, student_id=current_user.id,
        rating=data.rating, comment=data.comment,
    )

    return ReviewResponse(
        id=review.id,
        tutor_id=review.tutor_id,
        student_id=review.student_id,
        student_name=current_user.full_name,
        rating=review.rating,
        comment=review.comment,
    )


@router.get("/{tutor_id}/slots")
async def tutor_slots(
    tutor_id: int,
    days: int = Query(14, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Свободные слоты репетитора на N дней вперёд (по часу, 9:00–21:00)."""
    try:
        return await get_tutor_slots(db, tutor_id, days=days)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{tutor_id}/reviews", response_model=list[ReviewResponse])
async def list_reviews(tutor_id: int, db: AsyncSession = Depends(get_db)):
    """Список отзывов о репетиторе."""
    tutor = await get_tutor_by_id(db, tutor_id)
    if tutor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Репетитор не найден",
        )
    return await get_reviews(db, tutor_id)
