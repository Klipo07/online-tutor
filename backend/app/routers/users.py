"""Роутер пользователей — профиль, обновление, прогресс."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.progress import StudentProgress
from app.schemas.user import (
    UserUpdateRequest,
    UserFullResponse,
    ProgressResponse,
    UserProgressResponse,
)
from app.services.progress_service import (
    get_user_stats,
    get_test_history,
)

router = APIRouter()


@router.get("/me", response_model=UserFullResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Получить полный профиль текущего пользователя."""
    return current_user


@router.put("/me", response_model=UserFullResponse)
async def update_profile(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить профиль пользователя."""
    # Обновляем только переданные поля
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет данных для обновления",
        )

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/me/progress", response_model=UserProgressResponse)
async def get_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Прогресс пользователя по всем предметам."""
    query = (
        select(StudentProgress)
        .options(joinedload(StudentProgress.subject))
        .where(StudentProgress.user_id == current_user.id)
        .order_by(StudentProgress.last_activity.desc())
    )
    result = await db.execute(query)
    records = result.unique().scalars().all()

    progress = [
        ProgressResponse(
            subject_id=r.subject_id,
            subject_name=r.subject.name,
            score=r.score,
            weak_topics=r.weak_topics or [],
            last_activity=r.last_activity,
        )
        for r in records
    ]

    return UserProgressResponse(user_id=current_user.id, progress=progress)


@router.get("/me/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Общая статистика пользователя — тесты, чаты, занятия."""
    stats = await get_user_stats(db, current_user.id)
    return {"user_id": current_user.id, **stats}


@router.get("/me/test-history")
async def get_user_test_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """История прохождения тестов."""
    history = await get_test_history(db, current_user.id)
    return {"user_id": current_user.id, "history": history}
