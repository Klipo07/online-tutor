"""add working_hours to tutor_profiles

Revision ID: a0b1c2d3e4f5
Revises: e2f3a4b5c6d7
Create Date: 2026-04-18 02:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a0b1c2d3e4f5'
down_revision: Union[str, None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Дефолтное расписание: будни 9-21, суббота 10-18, воскресенье выходной (null)
DEFAULT_HOURS = (
    '{"mon":[9,21],"tue":[9,21],"wed":[9,21],"thu":[9,21],'
    '"fri":[9,21],"sat":[10,18],"sun":null}'
)


def upgrade() -> None:
    # Добавляем колонку nullable, заполняем значениями, потом делаем NOT NULL.
    # Отказались от server_default=sa.text() из-за конфликта двоеточия в :null
    # с биндпараметрами SQLAlchemy.
    op.add_column(
        'tutor_profiles',
        sa.Column(
            'working_hours',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE tutor_profiles SET working_hours = CAST(:hours AS JSONB)"
        ).bindparams(hours=DEFAULT_HOURS)
    )
    op.alter_column(
        'tutor_profiles', 'working_hours', nullable=False
    )


def downgrade() -> None:
    op.drop_column('tutor_profiles', 'working_hours')
