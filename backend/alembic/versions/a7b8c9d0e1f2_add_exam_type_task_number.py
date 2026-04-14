"""add exam_type and task_number to tests

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-04-14 13:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


exam_type_enum = sa.Enum("ege", "oge", "regular", name="examtype")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        exam_type_enum.create(bind, checkfirst=True)
        op.add_column(
            "tests",
            sa.Column(
                "exam_type",
                exam_type_enum,
                nullable=False,
                server_default="regular",
            ),
        )
    else:
        op.add_column(
            "tests",
            sa.Column(
                "exam_type",
                sa.String(length=16),
                nullable=False,
                server_default="regular",
            ),
        )

    op.add_column("tests", sa.Column("task_number", sa.Integer(), nullable=True))
    op.create_index("ix_tests_exam_type", "tests", ["exam_type"])
    op.create_index("ix_tests_task_number", "tests", ["task_number"])


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("ix_tests_task_number", table_name="tests")
    op.drop_index("ix_tests_exam_type", table_name="tests")
    op.drop_column("tests", "task_number")
    op.drop_column("tests", "exam_type")
    if bind.dialect.name == "postgresql":
        exam_type_enum.drop(bind, checkfirst=True)
