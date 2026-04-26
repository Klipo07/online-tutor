"""drop agora_channel_name from booking_sessions

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-04-26 00:00:00.000000

После задачи G (отказ от Agora в пользу meeting_link) колонка
`agora_channel_name` не используется. Удаляем как мёртвый код.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('booking_sessions', 'agora_channel_name')


def downgrade() -> None:
    op.add_column(
        'booking_sessions',
        sa.Column('agora_channel_name', sa.String(length=100), nullable=True),
    )
