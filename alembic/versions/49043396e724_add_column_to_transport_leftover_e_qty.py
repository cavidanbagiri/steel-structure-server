"""add_column_to_transport_leftover_e_qty

Revision ID: 49043396e724
Revises: 6e497d7dc8e4
Create Date: 2026-05-11 18:06:28.898313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49043396e724'
down_revision: Union[str, Sequence[str], None] = '6e497d7dc8e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('transports', sa.Column('t_leftover_qty', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('transports', 't_leftover_qty')

