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
    """Забронированное занятие с репетитором."""
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
    agora_channel_name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Связи
    student: Mapped["User"] = relationship(foreign_keys=[student_id])
    tutor: Mapped["TutorProfile"] = relationship(
        back_populates="booking_sessions", foreign_keys=[tutor_id]
    )
