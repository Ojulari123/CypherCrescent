"""add two_factor_enabled to users

Revision ID: b7d4f9a1c2e3
Revises: e5be5c1d2316
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d4f9a1c2e3'
down_revision: Union[str, Sequence[str], None] = 'e5be5c1d2316'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('two_factor_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'two_factor_enabled')
