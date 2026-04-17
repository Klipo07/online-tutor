"""drop bio column from tutor_profiles

Revision ID: a8b9c0d1e2f3
Revises: f6a7b8c9d0e1
Create Date: 2026-04-17 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a8b9c0d1e2f3'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Переносим bio из tutor_profiles в users (для существующих репетиторов)
    op.execute(
        """
        UPDATE users
        SET bio = tp.bio
        FROM tutor_profiles tp
        WHERE users.id = tp.user_id AND users.bio IS NULL AND tp.bio IS NOT NULL
        """
    )
    op.drop_column('tutor_profiles', 'bio')


def downgrade() -> None:
    op.add_column('tutor_profiles', sa.Column('bio', sa.Text(), nullable=True))
