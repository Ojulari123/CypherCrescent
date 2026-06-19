"""add price_alerts table

Revision ID: a1b2c3d4e5f6
Revises: e5be5c1d2316
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c3e8a2f6d401'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'price_alerts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('coin_slug', sa.String(100), nullable=False),
        sa.Column('target_price', sa.Numeric(24, 12), nullable=False),
        sa.Column('direction', sa.String(5), nullable=False),
        sa.Column('triggered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('triggered_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_price_alerts_user_id', 'price_alerts', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_price_alerts_user_id', table_name='price_alerts')
    op.drop_table('price_alerts')
