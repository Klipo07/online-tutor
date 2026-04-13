"""Модель пользователя."""

import enum
from datetime import date, datetime

from sqlalchemy import String, Enum, Date, DateTime, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    """Роли пользователей в системе."""
    student = "student"
    tutor = "tutor"
    parent = "parent"
    admin = "admin"


class User(Base):
    """Пользователь системы."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.student)
    first_name: Mapped[str] = mapped_column(String(75))
    last_name: Mapped[str] = mapped_column(String(75))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    birth_date: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Связи
    tutor_profile: Mapped["TutorProfile | None"] = relationship(
        back_populates="user", uselist=False
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user")
    progress: Mapped[list["StudentProgress"]] = relationship(back_populates="user")
    test_attempts: Mapped[list["TestAttempt"]] = relationship(back_populates="user")

    @hybrid_property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
