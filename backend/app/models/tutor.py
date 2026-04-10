"""Модель профиля репетитора."""

from sqlalchemy import ForeignKey, String, Text, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TutorProfile(Base):
    """Профиль репетитора — расширение пользователя с ролью tutor."""
    __tablename__ = "tutor_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    subjects: Mapped[list] = mapped_column(JSON, default=list)
    price_per_hour: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    experience_years: Mapped[int] = mapped_column(default=0)
    bio: Mapped[str | None] = mapped_column(Text)
    education: Mapped[str | None] = mapped_column(String(500))
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=0)
    reviews_count: Mapped[int] = mapped_column(default=0)
    is_verified: Mapped[bool] = mapped_column(default=False)

    # Связи
    user: Mapped["User"] = relationship(back_populates="tutor_profile")
    booking_sessions: Mapped[list["BookingSession"]] = relationship(
        back_populates="tutor", foreign_keys="BookingSession.tutor_id"
    )
    reviews: Mapped[list["Review"]] = relationship(back_populates="tutor")
