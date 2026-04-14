"""Роутер пользователей — профиль, обновление, прогресс."""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.progress import StudentProgress
from app.schemas.user import (
    PasswordChangeRequest,
    UserUpdateRequest,
    UserFullResponse,
    ProgressResponse,
    UserProgressResponse,
)
from app.services.auth_service import hash_password, verify_password
from app.services.progress_service import (
    get_activity_heatmap,
    get_user_stats,
    get_test_history,
)

AVATAR_DIR = Path(os.getenv("UPLOAD_DIR", "uploads")) / "avatars"
ALLOWED_AVATAR_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 МБ

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


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Смена пароля текущим пользователем."""
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль",
        )
    current_user.password_hash = hash_password(data.new_password)
    await db.commit()


@router.post("/me/avatar", response_model=UserFullResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Загрузить аватарку — jpg/png/webp, до 5 МБ."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_AVATAR_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только форматы JPG, PNG, WebP",
        )

    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Размер файла не должен превышать 5 МБ",
        )

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    dest = AVATAR_DIR / filename
    dest.write_bytes(content)

    current_user.avatar_url = f"/uploads/avatars/{filename}"
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


@router.get("/me/activity")
async def get_activity(
    days: int = 90,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Активность по дням за последние N дней — для heatmap."""
    days = max(7, min(days, 365))
    activity = await get_activity_heatmap(db, current_user.id, days)
    return {"user_id": current_user.id, "days": days, "activity": activity}


@router.get("/me/test-history")
async def get_user_test_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """История прохождения тестов."""
    history = await get_test_history(db, current_user.id)
    return {"user_id": current_user.id, "history": history}
