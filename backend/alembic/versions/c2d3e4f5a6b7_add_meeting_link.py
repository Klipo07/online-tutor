"""add meeting_link to booking_sessions

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-04-24 23:00:00.000000

Отказ от Agora: вместо встроенного видеозвонка репетитор присылает ссылку
на внешнюю платформу (Zoom / Google Meet / Jitsi). Колонка nullable — старые
занятия без ссылки остаются валидными.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'booking_sessions',
        sa.Column('meeting_link', sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('booking_sessions', 'meeting_link')
