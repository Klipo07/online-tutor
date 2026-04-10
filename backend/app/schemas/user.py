"""Pydantic-схемы для профиля и прогресса пользователя."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class UserUpdateRequest(BaseModel):
    """Запрос на обновление профиля."""
    full_name: str | None = Field(None, min_length=2, max_length=150)
    phone: str | None = Field(None, max_length=20)
    avatar_url: str | None = Field(None, max_length=500)
    birth_date: date | None = None


class UserFullResponse(BaseModel):
    """Полный профиль пользователя."""
    id: int
    email: str
    full_name: str
    role: str
    phone: str | None = None
    avatar_url: str | None = None
    birth_date: date | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProgressResponse(BaseModel):
    """Прогресс по одному предмету."""
    subject_id: int
    subject_name: str
    score: int
    weak_topics: list[str] = []
    last_activity: datetime

    model_config = {"from_attributes": True}


class UserProgressResponse(BaseModel):
    """Прогресс пользователя по всем предметам."""
    user_id: int
    progress: list[ProgressResponse]
