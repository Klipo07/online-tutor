"""Роутер видеозвонков — получение Agora токена, управление записью."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.booking import BookingStatus
from app.schemas.video import (
    VideoTokenRequest,
    VideoTokenResponse,
    RecordingStartRequest,
    RecordingResponse,
)
from app.services.session_service import get_session_by_id
from app.services.video_service import generate_agora_token

router = APIRouter()


@router.post("/token", response_model=VideoTokenResponse)
async def get_video_token(
    data: VideoTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить Agora-токен для подключения к видеозвонку.

    Доступно только участникам занятия (ученик или репетитор).
    Занятие должно быть в статусе pending или confirmed.
    """
    booking = await get_session_by_id(db, data.session_id)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Занятие не найдено",
        )

    # Проверяем что пользователь — участник
    is_student = booking.student_id == current_user.id
    is_tutor = booking.tutor.user_id == current_user.id
    if not is_student and not is_tutor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь участником этого занятия",
        )

    # Проверяем статус занятия
    if booking.status not in (BookingStatus.pending, BookingStatus.confirmed):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Занятие недоступно для видеозвонка",
        )

    # Переводим в confirmed при первом подключении
    if booking.status == BookingStatus.pending:
        booking.status = BookingStatus.confirmed
        await db.commit()

    # Генерируем токен — uid = user.id для идентификации
    token = generate_agora_token(
        channel_name=booking.agora_channel_name,
        uid=current_user.id,
        expire_seconds=booking.duration_minutes * 60 + 600,  # +10 мин запас
    )

    return VideoTokenResponse(
        token=token,
        channel_name=booking.agora_channel_name,
        uid=current_user.id,
        app_id=settings.AGORA_APP_ID,
    )


@router.post("/recording/start", response_model=RecordingResponse)
async def start_recording(
    data: RecordingStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Начать запись занятия.

    В MVP записывается только факт — полноценная запись через
    Agora Cloud Recording будет в следующей версии.
    """
    booking = await get_session_by_id(db, data.session_id)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Занятие не найдено",
        )

    # Только участники могут начать запись
    is_student = booking.student_id == current_user.id
    is_tutor = booking.tutor.user_id == current_user.id
    if not is_student and not is_tutor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь участником этого занятия",
        )

    if booking.status != BookingStatus.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Занятие должно быть подтверждено для начала записи",
        )

    # В MVP — логируем, полноценная запись в v2
    return RecordingResponse(
        session_id=booking.id,
        status="started",
        message="Запись занятия начата (MVP: только метаданные, полная запись в v2)",
    )
