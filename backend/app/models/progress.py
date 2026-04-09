"""Модель прогресса ученика."""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StudentProgress(Base):
    """Прогресс ученика по предмету/теме."""
    __tablename__ = "student_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"))
    score: Mapped[int] = mapped_column(Integer, default=0)
    weak_topics: Mapped[list] = mapped_column(JSON, default=list)
    last_activity: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Связи
    user: Mapped["User"] = relationship(back_populates="progress")
