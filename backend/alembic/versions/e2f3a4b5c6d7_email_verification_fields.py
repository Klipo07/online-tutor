"""add email verification fields to users

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-04-17 16:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('email_verified_at', sa.DateTime(), nullable=True),
    )
    op.add_column(
        'users',
        sa.Column('email_verify_token_hash', sa.String(length=64), nullable=True),
    )
    op.add_column(
        'users',
        sa.Column('email_verify_token_expires_at', sa.DateTime(), nullable=True),
    )
    op.add_column(
        'users',
        sa.Column('last_verification_sent_at', sa.DateTime(), nullable=True),
    )
    op.create_index(
        'ix_users_email_verify_token_hash',
        'users',
        ['email_verify_token_hash'],
    )


def downgrade() -> None:
    op.drop_index('ix_users_email_verify_token_hash', table_name='users')
    op.drop_column('users', 'last_verification_sent_at')
    op.drop_column('users', 'email_verify_token_expires_at')
    op.drop_column('users', 'email_verify_token_hash')
    op.drop_column('users', 'email_verified_at')
