"""Роутер пользователей — профиль, прогресс."""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Получить профиль текущего пользователя (требует авторизации)."""
    return current_user


@router.put("/me")
async def update_profile(current_user: User = Depends(get_current_user)):
    """Обновить профиль."""
    return {"message": "update profile — TODO"}


@router.get("/me/progress")
async def get_progress(current_user: User = Depends(get_current_user)):
    """Прогресс по предметам."""
    return {"message": "progress — TODO"}
