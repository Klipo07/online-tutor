"""Pydantic-схемы для авторизации."""

import re
from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator


_PASSWORD_LETTER = re.compile(r"[A-Za-zА-Яа-яЁё]")
_PASSWORD_UPPER = re.compile(r"[A-ZА-ЯЁ]")


def _validate_password_strength(value: str) -> str:
    """Валидатор силы пароля: минимум 6 символов, 1 буква, 1 заглавная."""
    if len(value) < 6:
        raise ValueError("Пароль должен содержать минимум 6 символов")
    if not _PASSWORD_LETTER.search(value):
        raise ValueError("Пароль должен содержать хотя бы одну букву")
    if not _PASSWORD_UPPER.search(value):
        raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
    return value


class _RegisterBase(BaseModel):
    """Общие поля для всех типов регистрации."""
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    first_name: str = Field(min_length=2, max_length=75)
    last_name: str = Field(min_length=2, max_length=75)

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class RegisterStudent(_RegisterBase):
    """Регистрация ученика или родителя."""
    # Без default — discriminator требует явное значение role от клиента
    role: Literal["student", "parent"]


class RegisterTutor(_RegisterBase):
    """Регистрация репетитора — дополнительно профиль TutorProfile."""
    role: Literal["tutor"]
    subjects: list[str] = Field(min_length=1, description="Минимум один предмет")
    price_per_hour: float = Field(ge=0, le=100000, description="Цена за час, руб.")
    experience_years: int = Field(ge=0, le=70, description="Стаж в годах")
    bio: str | None = Field(default=None, max_length=500, description="О себе")
    education: str | None = Field(default=None, max_length=500, description="Образование")


# Discriminated union — Pydantic v2 выбирает схему по полю `role`
RegisterRequest = Annotated[
    Union[RegisterStudent, RegisterTutor],
    Field(discriminator="role"),
]


class LoginRequest(BaseModel):
    """Запрос на вход."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Ответ с JWT-токенами."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Запрос на обновление токена."""
    refresh_token: str


class UserResponse(BaseModel):
    """Данные пользователя в ответе."""
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    avatar_url: str | None = None
    email_verified_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @computed_field
    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None


class AuthResponse(BaseModel):
    """Ответ при регистрации/входе — токены + пользователь."""
    user: UserResponse
    tokens: TokenResponse
