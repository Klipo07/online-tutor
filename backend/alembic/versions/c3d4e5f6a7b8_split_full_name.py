"""split full_name into first_name and last_name

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-13 11:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Идентификаторы ревизии
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Добавляем новые колонки (nullable, чтобы сначала заполнить данными)
    op.add_column('users', sa.Column('first_name', sa.String(length=75), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(length=75), nullable=True))

    # 2) Переносим данные: разбиваем full_name по первому пробелу
    op.execute(
        """
        UPDATE users
        SET first_name = split_part(full_name, ' ', 1),
            last_name  = CASE
                WHEN position(' ' in full_name) > 0
                    THEN substring(full_name from position(' ' in full_name) + 1)
                ELSE '-'
            END
        """
    )

    # 3) Делаем NOT NULL
    op.alter_column('users', 'first_name', nullable=False)
    op.alter_column('users', 'last_name', nullable=False)

    # 4) Удаляем старую колонку
    op.drop_column('users', 'full_name')


def downgrade() -> None:
    op.add_column('users', sa.Column('full_name', sa.String(length=150), nullable=True))
    op.execute("UPDATE users SET full_name = first_name || ' ' || last_name")
    op.alter_column('users', 'full_name', nullable=False)
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
