"""Сервис бронирования занятий — создание, отмена, список."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.booking import BookingSession, BookingStatus, PaymentStatus
from app.models.tutor import TutorProfile
from app.models.subject import Subject


async def create_booking(
    db: AsyncSession,
    student_id: int,
    tutor_id: int,
    subject_id: int,
    scheduled_at: datetime,
    duration_minutes: int,
) -> BookingSession:
    """Создать бронирование занятия."""
    # Получаем профиль репетитора для расчёта цены
    tutor = await db.get(TutorProfile, tutor_id)
    if tutor is None:
        raise ValueError("Репетитор не найден")

    # Нельзя записаться к самому себе
    if tutor.user_id == student_id:
        raise ValueError("Нельзя записаться к самому себе")

    # Проверяем что предмет существует
    subject = await db.get(Subject, subject_id)
    if subject is None:
        raise ValueError("Предмет не найден")

    # Проверяем что время не в прошлом (храним naive UTC, совпадает с scheduled_at из Pydantic)
    now_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    if scheduled_at < now_utc_naive:
        raise ValueError("Нельзя забронировать занятие в прошлом")

    # Проверяем пересечение времени — пересечение считаем в Python,
    # чтобы SQL-запрос работал на любом диалекте (PostgreSQL/SQLite)
    end_time = scheduled_at + timedelta(minutes=duration_minutes)
    active_bookings = await db.execute(
        select(BookingSession).where(
            BookingSession.tutor_id == tutor_id,
            BookingSession.status.in_([BookingStatus.pending, BookingStatus.confirmed]),
            BookingSession.scheduled_at < end_time,
        )
    )
    for existing in active_bookings.scalars():
        existing_end = existing.scheduled_at + timedelta(minutes=existing.duration_minutes)
        if existing_end > scheduled_at:
            raise ValueError("У репетитора уже есть занятие на это время")

    # Рассчитываем стоимость
    price = float(tutor.price_per_hour) * duration_minutes / 60

    # Генерируем уникальное имя канала для видеозвонка
    channel_name = f"session-{uuid.uuid4().hex[:12]}"

    booking = BookingSession(
        student_id=student_id,
        tutor_id=tutor_id,
        subject_id=subject_id,
        scheduled_at=scheduled_at,
        duration_minutes=duration_minutes,
        status=BookingStatus.pending,
        price=price,
        payment_status=PaymentStatus.pending,
        agora_channel_name=channel_name,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


async def get_user_sessions(
    db: AsyncSession,
    user_id: int,
    status_filter: str | None = None,
) -> list[BookingSession]:
    """Получить все занятия пользователя (как ученика или репетитора)."""
    # Находим tutor_profile_id пользователя (если есть)
    tutor_query = select(TutorProfile.id).where(TutorProfile.user_id == user_id)
    tutor_result = await db.execute(tutor_query)
    tutor_profile_id = tutor_result.scalar_one_or_none()

    # Ищем занятия где пользователь — ученик ИЛИ репетитор
    query = select(BookingSession).options(
        joinedload(BookingSession.tutor).joinedload(TutorProfile.user),
        joinedload(BookingSession.subject),
    )

    if tutor_profile_id:
        query = query.where(
            or_(
                BookingSession.student_id == user_id,
                BookingSession.tutor_id == tutor_profile_id,
            )
        )
    else:
        query = query.where(BookingSession.student_id == user_id)

    if status_filter:
        query = query.where(BookingSession.status == status_filter)

    query = query.order_by(BookingSession.scheduled_at.desc())

    result = await db.execute(query)
    return result.unique().scalars().all()


async def get_session_by_id(
    db: AsyncSession,
    session_id: int,
) -> BookingSession | None:
    """Получить занятие по ID с загрузкой связей."""
    query = (
        select(BookingSession)
        .options(
            joinedload(BookingSession.tutor).joinedload(TutorProfile.user),
            joinedload(BookingSession.subject),
        )
        .where(BookingSession.id == session_id)
    )
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


async def get_tutor_slots(
    db: AsyncSession,
    tutor_id: int,
    days: int = 14,
) -> list[dict]:
    """Вернуть свободные слоты репетитора на N дней вперёд.

    Простая эвристика MVP: рабочие часы 9:00–21:00 по часу,
    исключаем уже забронированные слоты.
    """
    tutor = await db.get(TutorProfile, tutor_id)
    if tutor is None:
        raise ValueError("Репетитор не найден")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today = now.date()
    horizon_end = datetime.combine(today + timedelta(days=days), datetime.min.time())

    # Забираем все активные брони в горизонте
    bookings_query = select(BookingSession).where(
        BookingSession.tutor_id == tutor_id,
        BookingSession.status.in_([BookingStatus.pending, BookingStatus.confirmed]),
        BookingSession.scheduled_at >= now - timedelta(hours=3),
        BookingSession.scheduled_at < horizon_end,
    )
    bookings_result = await db.execute(bookings_query)
    busy_starts = {b.scheduled_at.replace(second=0, microsecond=0) for b in bookings_result.scalars()}

    slots_by_day: list[dict] = []
    for d in range(days):
        day = today + timedelta(days=d)
        day_slots = []
        for hour in range(9, 21):
            slot_dt = datetime.combine(day, datetime.min.time()).replace(hour=hour)
            if slot_dt <= now:
                continue
            available = slot_dt not in busy_starts
            day_slots.append({
                "time": slot_dt.strftime("%H:%M"),
                "datetime": slot_dt.isoformat(),
                "available": available,
            })
        if day_slots:
            slots_by_day.append({
                "date": day.isoformat(),
                "slots": day_slots,
            })
    return slots_by_day


async def cancel_booking(
    db: AsyncSession,
    session_id: int,
    user_id: int,
) -> BookingSession:
    """Отменить бронирование."""
    booking = await get_session_by_id(db, session_id)

    if booking is None:
        raise ValueError("Занятие не найдено")

    # Проверяем что пользователь — участник занятия
    is_student = booking.student_id == user_id
    is_tutor = booking.tutor.user_id == user_id
    if not is_student and not is_tutor:
        raise PermissionError("Вы не можете отменить это занятие")

    # Проверяем статус
    if booking.status == BookingStatus.cancelled:
        raise ValueError("Занятие уже отменено")
    if booking.status == BookingStatus.completed:
        raise ValueError("Нельзя отменить завершённое занятие")

    booking.status = BookingStatus.cancelled

    # Если было оплачено — ставим статус возврата
    if booking.payment_status == PaymentStatus.paid:
        booking.payment_status = PaymentStatus.refunded

    await db.commit()
    await db.refresh(booking)
    return booking
