"""add unique user_coin on holdings

Revision ID: e5be5c1d2316
Revises: 48e9ec8307e1
Create Date: 2026-06-17 19:11:19.471099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5be5c1d2316'
down_revision: Union[str, Sequence[str], None] = '48e9ec8307e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('uq_holdings_user_coin', 'holdings', ['user_id', 'coin_slug'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_holdings_user_coin', 'holdings', type_='unique')
