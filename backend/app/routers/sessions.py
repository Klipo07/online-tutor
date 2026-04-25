"""Роутер занятий — бронирование, список, детали, отмена."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.session import (
    SessionCreateRequest,
    SessionResponse,
    SessionListResponse,
    SessionCancelRequest,
    SessionCancelResponse,
    MeetingLinkUpdate,
)
from app.services.session_service import (
    BookingAlreadyStartedError,
    create_booking,
    get_user_sessions,
    get_session_by_id,
    cancel_booking,
)
from app.models.tutor import TutorProfile
from sqlalchemy import select

router = APIRouter()


def _session_to_response(booking) -> SessionResponse:
    """Преобразовать BookingSession в SessionResponse."""
    return SessionResponse(
        id=booking.id,
        student_id=booking.student_id,
        tutor_id=booking.tutor_id,
        subject_id=booking.subject_id,
        tutor_name=booking.tutor.user.full_name,
        student_name=booking.student.full_name if booking.student else "",
        subject_name=booking.subject.name,
        scheduled_at=booking.scheduled_at,
        duration_minutes=booking.duration_minutes,
        status=booking.status.value,
        price=float(booking.price),
        payment_status=booking.payment_status.value,
        agora_channel_name=booking.agora_channel_name,
        meeting_link=booking.meeting_link,
        created_at=booking.created_at,
    )


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать бронирование занятия с репетитором."""
    try:
        booking = await create_booking(
            db,
            student_id=current_user.id,
            tutor_id=data.tutor_id,
            subject_id=data.subject_id,
            scheduled_at=data.scheduled_at,
            duration_minutes=data.duration_minutes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Перезагружаем с join для ответа
    booking = await get_session_by_id(db, booking.id)
    return _session_to_response(booking)


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    status_filter: str | None = Query(
        None, alias="status",
        description="Фильтр по статусу: pending, confirmed, completed, cancelled",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список занятий текущего пользователя."""
    sessions = await get_user_sessions(db, current_user.id, status_filter)
    return SessionListResponse(
        sessions=[_session_to_response(s) for s in sessions],
        total=len(sessions),
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Детали конкретного занятия."""
    booking = await get_session_by_id(db, session_id)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Занятие не найдено",
        )

    # Проверяем доступ — только участники
    is_student = booking.student_id == current_user.id
    is_tutor = booking.tutor.user_id == current_user.id
    if not is_student and not is_tutor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет доступа к этому занятию",
        )

    return _session_to_response(booking)


@router.put("/{session_id}/cancel", response_model=SessionCancelResponse)
async def cancel_session(
    session_id: int,
    data: SessionCancelRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отмена бронирования занятия.

    Тело `{"reason": "..."}` опционально. Обязательно при отмене за <24 часа.
    Занятия, уже начавшиеся, отменить нельзя — возвращается 409.
    """
    reason = data.reason if data else None
    try:
        booking = await cancel_booking(db, session_id, current_user.id, reason=reason)
    except BookingAlreadyStartedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    return SessionCancelResponse(
        id=booking.id,
        status=booking.status.value,
        message="Занятие успешно отменено",
        cancellation_reason=booking.cancellation_reason,
    )


@router.put("/{session_id}/meeting-link", response_model=SessionResponse)
async def set_meeting_link(
    session_id: int,
    data: MeetingLinkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Установить / очистить ссылку на внешнюю платформу видеозвонка.

    Только репетитор этого занятия может менять meeting_link.
    Передайте пустую строку или null чтобы очистить.
    """
    booking = await get_session_by_id(db, session_id)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Занятие не найдено",
        )

    # Проверяем что текущий user — репетитор этого занятия
    tutor_user_id = await db.scalar(
        select(TutorProfile.user_id).where(TutorProfile.id == booking.tutor_id)
    )
    if tutor_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только репетитор может установить ссылку",
        )

    # Очистка: пустая строка → NULL
    link = (data.meeting_link or "").strip()
    booking.meeting_link = link or None
    await db.commit()
    await db.refresh(booking)
    # Перезагружаем с join для ответа
    booking = await get_session_by_id(db, session_id)
    return _session_to_response(booking)
