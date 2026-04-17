"""add cancellation fields to booking_sessions

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
Create Date: 2026-04-17 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c0d1e2f3a4b5'
down_revision: Union[str, None] = 'b9c0d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'booking_sessions',
        sa.Column('cancellation_reason', sa.String(length=500), nullable=True),
    )
    op.add_column(
        'booking_sessions',
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
    )
    op.add_column(
        'booking_sessions',
        sa.Column(
            'cancelled_by_user_id',
            sa.Integer(),
            sa.ForeignKey('users.id'),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column('booking_sessions', 'cancelled_by_user_id')
    op.drop_column('booking_sessions', 'cancelled_at')
    op.drop_column('booking_sessions', 'cancellation_reason')
