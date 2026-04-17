"""add test_feedbacks table

Revision ID: d1e2f3a4b5c6
Revises: c0d1e2f3a4b5
Create Date: 2026-04-17 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c0d1e2f3a4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


feedback_rating_enum = sa.Enum(
    'too_easy', 'ok', 'too_hard',
    name='feedbackrating',
)


def upgrade() -> None:
    op.create_table(
        'test_feedbacks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('test_id', sa.Integer(), sa.ForeignKey('tests.id'), nullable=False),
        sa.Column('rating', feedback_rating_enum, nullable=False),
        sa.Column('comment', sa.String(length=500), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
    )
    op.create_index(
        'ix_test_feedbacks_user_id', 'test_feedbacks', ['user_id'],
    )
    op.create_index(
        'ix_test_feedbacks_test_id', 'test_feedbacks', ['test_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_test_feedbacks_test_id', table_name='test_feedbacks')
    op.drop_index('ix_test_feedbacks_user_id', table_name='test_feedbacks')
    op.drop_table('test_feedbacks')
    feedback_rating_enum.drop(op.get_bind(), checkfirst=True)
