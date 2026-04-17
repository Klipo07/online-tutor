"""add GIN index on tutor_profiles.subjects for JSONB @> filtering

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-04-17 11:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b9c0d1e2f3a4'
down_revision: Union[str, None] = 'a8b9c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Переводим JSON-колонку в JSONB и добавляем GIN-индекс для быстрого @> поиска
    # по предметам. Оператор `@>` в PostgreSQL работает только с jsonb.
    op.execute(
        "ALTER TABLE tutor_profiles "
        "ALTER COLUMN subjects TYPE jsonb USING subjects::jsonb"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tutor_profiles_subjects_gin "
        "ON tutor_profiles USING GIN (subjects)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tutor_profiles_subjects_gin")
    op.execute(
        "ALTER TABLE tutor_profiles "
        "ALTER COLUMN subjects TYPE json USING subjects::json"
    )
