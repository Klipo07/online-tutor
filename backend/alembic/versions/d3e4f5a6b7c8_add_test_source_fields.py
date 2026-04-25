"""add source_url, external_id, image_paths to tests

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-04-25 18:00:00.000000

Импорт заданий с sdamgia (Решу ЕГЭ): храним внешний ID для идемпотентности
повторного запуска скрипта, source_url для бэк-ссылки, image_paths для
графиков/чертежей (формулы остаются в тексте через alt-атрибут SVG).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tests', sa.Column('source_url', sa.String(length=500), nullable=True))
    op.add_column('tests', sa.Column('external_id', sa.String(length=50), nullable=True))
    op.add_column('tests', sa.Column('image_paths', sa.JSON(), nullable=True))
    # Уникальный индекс по external_id — чтобы повторный импорт не плодил дубли
    op.create_index(
        'ix_tests_external_id',
        'tests',
        ['external_id'],
        unique=True,
        postgresql_where=sa.text('external_id IS NOT NULL'),
    )


def downgrade() -> None:
    op.drop_index('ix_tests_external_id', table_name='tests')
    op.drop_column('tests', 'image_paths')
    op.drop_column('tests', 'external_id')
    op.drop_column('tests', 'source_url')
