"""Модель бронирования занятий с репетитором."""

import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Integer, Numeric, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BookingStatus(str, enum.Enum):
    """Статус бронирования."""
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class PaymentStatus(str, enum.Enum):
    """Статус оплаты."""
    pending = "pending"
    paid = "paid"
    refunded = "refunded"


class BookingSession(Base):
    """Забронированное занятие с репетитором.

    Отмена реализована как soft-delete через статус `cancelled`, с сохранением
    причины и автора отмены — это нужно и для истории, и для потенциального
    возврата оплаты.
    """
    __tablename__ = "booking_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutor_profiles.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), default=BookingStatus.pending
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.pending
    )
    # Ссылка на внешнюю платформу видеозвонка (Zoom/Meet/Jitsi) — заполняется тьютором
    meeting_link: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Поля отмены
    cancellation_reason: Mapped[str | None] = mapped_column(String(500))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancelled_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # Связи
    student: Mapped["User"] = relationship(foreign_keys=[student_id])
    tutor: Mapped["TutorProfile"] = relationship(
        back_populates="booking_sessions", foreign_keys=[tutor_id]
    )
    subject: Mapped["Subject"] = relationship()
