"""Pydantic-схемы для бронирования занятий."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionCreateRequest(BaseModel):
    """Запрос на бронирование занятия."""
    tutor_id: int
    subject_id: int
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=30, le=180)


class SessionResponse(BaseModel):
    """Данные занятия в ответе."""
    id: int
    student_id: int
    tutor_id: int
    subject_id: int
    tutor_name: str
    subject_name: str
    scheduled_at: datetime
    duration_minutes: int
    status: str
    price: float
    payment_status: str
    agora_channel_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    """Список занятий."""
    sessions: list[SessionResponse]
    total: int


class SessionCancelResponse(BaseModel):
    """Ответ при отмене занятия."""
    id: int
    status: str
    message: str
