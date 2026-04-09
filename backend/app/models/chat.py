"""Модели чата с AI-тьютором."""

import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, Enum, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AIProvider(str, enum.Enum):
    """Провайдер AI."""
    openai = "openai"
    anthropic = "anthropic"


class MessageRole(str, enum.Enum):
    """Роль автора сообщения."""
    user = "user"
    assistant = "assistant"


class ChatSession(Base):
    """Сессия чата с AI-тьютором."""
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id"))
    topic: Mapped[str | None] = mapped_column(String(300))
    provider: Mapped[AIProvider] = mapped_column(Enum(AIProvider), default=AIProvider.openai)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Связи
    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    """Отдельное сообщение в чате."""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"))
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole))
    content: Mapped[str] = mapped_column(Text)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Связи
    session: Mapped["ChatSession"] = relationship(back_populates="messages")
