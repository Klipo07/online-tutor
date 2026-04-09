"""Модели предметов и тем."""

from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Subject(Base):
    """Учебный предмет."""
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(50))

    # Связи
    topics: Mapped[list["Topic"]] = relationship(back_populates="subject")


class Topic(Base):
    """Тема внутри предмета."""
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    name: Mapped[str] = mapped_column(String(200))
    order: Mapped[int] = mapped_column(default=0)

    # Связи
    subject: Mapped["Subject"] = relationship(back_populates="topics")
