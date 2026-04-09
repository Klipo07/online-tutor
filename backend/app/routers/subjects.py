"""Роутер предметов — список предметов и тем."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_subjects():
    """Список всех предметов."""
    return {"message": "subjects list — TODO"}


@router.get("/{subject_id}/topics")
async def get_topics(subject_id: int):
    """Темы по предмету."""
    return {"message": f"topics for subject {subject_id} — TODO"}
