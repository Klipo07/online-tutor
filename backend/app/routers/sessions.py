"""Роутер занятий — бронирование, список, отмена."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_session():
    """Создать бронирование занятия."""
    return {"message": "create session — TODO"}


@router.get("/")
async def list_sessions():
    """Мои занятия."""
    return {"message": "sessions list — TODO"}


@router.get("/{session_id}")
async def get_session(session_id: int):
    """Детали занятия."""
    return {"message": f"session {session_id} — TODO"}


@router.put("/{session_id}/cancel")
async def cancel_session(session_id: int):
    """Отмена занятия."""
    return {"message": f"cancel session {session_id} — TODO"}
