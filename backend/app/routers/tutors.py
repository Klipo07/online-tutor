"""Роутер репетиторов — список, профиль, отзывы."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.tutor import (
    TutorResponse,
    TutorListResponse,
    ReviewCreate,
    ReviewResponse,
)
from app.services.tutor_service import (
    get_tutors,
    get_tutor_by_id,
    create_review,
    get_reviews,
)

router = APIRouter()


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
