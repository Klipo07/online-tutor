"""add performance indexes

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-13 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


# Идентификаторы ревизии
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Индексы на часто используемые FK-поля — ускоряют JOIN и выборку по пользователю
INDEXES = [
    ("ix_chat_sessions_user_id", "chat_sessions", "user_id"),
    ("ix_chat_sessions_subject_id", "chat_sessions", "subject_id"),
    ("ix_chat_messages_session_id", "chat_messages", "session_id"),
    ("ix_booking_sessions_student_id", "booking_sessions", "student_id"),
    ("ix_booking_sessions_tutor_id", "booking_sessions", "tutor_id"),
    ("ix_booking_sessions_scheduled_at", "booking_sessions", "scheduled_at"),
    ("ix_student_progress_user_id", "student_progress", "user_id"),
    ("ix_student_progress_subject_id", "student_progress", "subject_id"),
    ("ix_test_attempts_user_id", "test_attempts", "user_id"),
    ("ix_test_attempts_test_id", "test_attempts", "test_id"),
    ("ix_tests_subject_id", "tests", "subject_id"),
    ("ix_reviews_tutor_id", "reviews", "tutor_id"),
    ("ix_reviews_student_id", "reviews", "student_id"),
]


def upgrade() -> None:
    for name, table, column in INDEXES:
        op.create_index(name, table, [column])


def downgrade() -> None:
    for name, table, _ in INDEXES:
        op.drop_index(name, table_name=table)
