"""Pydantic-схемы для авторизации."""

import re

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


class RegisterRequest(BaseModel):
    """Запрос на регистрацию."""
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    first_name: str = Field(min_length=2, max_length=75)
    last_name: str = Field(min_length=2, max_length=75)
    role: str = Field(default="student", pattern="^(student|tutor|parent)$")

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return _validate_password_strength(v)


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

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class AuthResponse(BaseModel):
    """Ответ при регистрации/входе — токены + пользователь."""
    user: UserResponse
    tokens: TokenResponse
