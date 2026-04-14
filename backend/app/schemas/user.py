"""Pydantic-схемы для профиля и прогресса пользователя."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.schemas.auth import _validate_password_strength


class UserUpdateRequest(BaseModel):
    """Запрос на обновление профиля."""
    first_name: str | None = Field(None, min_length=2, max_length=75)
    last_name: str | None = Field(None, min_length=2, max_length=75)
    phone: str | None = Field(None, max_length=20)
    avatar_url: str | None = Field(None, max_length=500)
    bio: str | None = Field(None, max_length=500)
    birth_date: date | None = None


class PasswordChangeRequest(BaseModel):
    """Запрос на смену пароля."""
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserFullResponse(BaseModel):
    """Полный профиль пользователя."""
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    phone: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    birth_date: date | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class ProgressResponse(BaseModel):
    """Прогресс по одному предмету."""
    subject_id: int
    subject_name: str
    score: int
    weak_topics: list[str] = []
    last_activity: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProgressResponse(BaseModel):
    """Прогресс пользователя по всем предметам."""
    user_id: int
    progress: list[ProgressResponse]
