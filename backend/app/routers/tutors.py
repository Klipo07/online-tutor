"""Роутер репетиторов — список, профиль, отзывы."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_tutors():
    """Список репетиторов с фильтрами."""
    return {"message": "tutors list — TODO"}


@router.get("/{tutor_id}")
async def get_tutor(tutor_id: int):
    """Профиль репетитора."""
    return {"message": f"tutor {tutor_id} — TODO"}


@router.post("/{tutor_id}/review")
async def create_review(tutor_id: int):
    """Оставить отзыв о репетиторе."""
    return {"message": f"review for tutor {tutor_id} — TODO"}
