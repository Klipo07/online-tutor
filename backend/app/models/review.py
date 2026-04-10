"""Модель отзывов о репетиторах."""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Review(Base):
    """Отзыв ученика о репетиторе."""
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutor_profiles.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Связи
    tutor: Mapped["TutorProfile"] = relationship(back_populates="reviews")
    student: Mapped["User"] = relationship()
