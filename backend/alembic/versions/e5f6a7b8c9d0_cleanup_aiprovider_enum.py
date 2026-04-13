"""cleanup aiprovider enum — keep only anthropic/yandex

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-13 13:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


# Идентификаторы ревизии
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Оставляем только anthropic и yandex. Старые значения конвертируем в anthropic."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # На SQLite и других enum — это просто строка, миграция не нужна
        return

    # Приводим устаревшие значения к anthropic
    op.execute(
        "UPDATE chat_sessions SET provider = 'anthropic' "
        "WHERE provider IN ('openai', 'gemini', 'openrouter')"
    )

    # Создаём новый enum и переключаем колонку
    op.execute("ALTER TYPE aiprovider RENAME TO aiprovider_old")
    op.execute("CREATE TYPE aiprovider AS ENUM ('anthropic', 'yandex')")
    op.execute(
        "ALTER TABLE chat_sessions ALTER COLUMN provider TYPE aiprovider "
        "USING provider::text::aiprovider"
    )
    op.execute("ALTER TABLE chat_sessions ALTER COLUMN provider SET DEFAULT 'anthropic'")
    op.execute("DROP TYPE aiprovider_old")


def downgrade() -> None:
    """Возвращаем enum с openai/anthropic/gemini/openrouter/yandex."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("ALTER TYPE aiprovider RENAME TO aiprovider_new")
    op.execute(
        "CREATE TYPE aiprovider AS ENUM "
        "('openai', 'anthropic', 'gemini', 'openrouter', 'yandex')"
    )
    op.execute(
        "ALTER TABLE chat_sessions ALTER COLUMN provider TYPE aiprovider "
        "USING provider::text::aiprovider"
    )
    op.execute("ALTER TABLE chat_sessions ALTER COLUMN provider SET DEFAULT 'openai'")
    op.execute("DROP TYPE aiprovider_new")
