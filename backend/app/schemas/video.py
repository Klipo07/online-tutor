"""Pydantic-схемы для видеозвонков."""

from pydantic import BaseModel, Field


class VideoTokenRequest(BaseModel):
    """Запрос на получение токена для видеозвонка."""
    session_id: int = Field(description="ID забронированного занятия")


class VideoTokenResponse(BaseModel):
    """Ответ с токеном и данными для подключения."""
    token: str
    channel_name: str
    uid: int
    app_id: str


class RecordingStartRequest(BaseModel):
    """Запрос на начало записи занятия."""
    session_id: int


class RecordingResponse(BaseModel):
    """Ответ о статусе записи."""
    session_id: int
    status: str
    message: str
