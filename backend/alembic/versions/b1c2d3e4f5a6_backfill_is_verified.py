"""backfill is_verified=True for all tutor profiles

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-04-24 10:00:00.000000

Одноразовый бэкфилл: до фикса в auth_service.py новые репетиторы
создавались с is_verified=False и не попадали в маркетплейс.
SMTP-верификация не настроена, поэтому включаем всех принудительно.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a0b1c2d3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE tutor_profiles SET is_verified = true WHERE is_verified = false")


def downgrade() -> None:
    # Откат намеренно no-op: данные пользователей не сбрасываем
    pass
