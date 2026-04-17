"""Модели тестов и попыток прохождения."""

import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, Integer, JSON, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Difficulty(str, enum.Enum):
    """Уровень сложности теста."""
    easy = "easy"
    medium = "medium"
    hard = "hard"


class ExamType(str, enum.Enum):
    """Формат теста — ЕГЭ, ОГЭ или обычный."""
    ege = "ege"
    oge = "oge"
    regular = "regular"


class Test(Base):
    """Тест, сгенерированный AI или созданный вручную."""
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    topic: Mapped[str] = mapped_column(String(300))
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.medium)
    exam_type: Mapped[ExamType] = mapped_column(
        Enum(ExamType), default=ExamType.regular, index=True
    )
    task_number: Mapped[int | None] = mapped_column(Integer, index=True)
    questions: Mapped[dict] = mapped_column(JSON)
    created_by_ai: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Связи
    attempts: Mapped[list["TestAttempt"]] = relationship(back_populates="test")


class TestAttempt(Base):
    """Попытка прохождения теста пользователем."""
    __tablename__ = "test_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    answers: Mapped[dict] = mapped_column(JSON)
    score: Mapped[int] = mapped_column(Integer, default=0)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer)
    feedback_from_ai: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Связи
    user: Mapped["User"] = relationship(back_populates="test_attempts")
    test: Mapped["Test"] = relationship(back_populates="attempts")


class FeedbackRating(str, enum.Enum):
    """Оценка сложности теста пользователем — для автокоррекции."""
    too_easy = "too_easy"
    ok = "ok"
    too_hard = "too_hard"


class TestFeedback(Base):
    """Фидбек пользователя после прохождения теста."""
    __tablename__ = "test_feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"), index=True)
    rating: Mapped[FeedbackRating] = mapped_column(Enum(FeedbackRating))
    comment: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
