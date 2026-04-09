"""Роутер видеозвонков — Agora токен, запись."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/token")
async def get_video_token():
    """Получить Agora токен для видеозвонка."""
    return {"message": "video token — TODO"}


@router.post("/recording/start")
async def start_recording():
    """Начать запись занятия."""
    return {"message": "start recording — TODO"}
