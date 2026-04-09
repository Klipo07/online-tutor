"""Pydantic-схемы для авторизации."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Запрос на регистрацию."""
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    full_name: str = Field(min_length=2, max_length=150)
    role: str = Field(default="student", pattern="^(student|tutor|parent)$")


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
    full_name: str
    role: str
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Ответ при регистрации/входе — токены + пользователь."""
    user: UserResponse
    tokens: TokenResponse
