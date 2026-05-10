"""add_column_to_main_leftoverqty

Revision ID: 9c5383fb65c4
Revises: 7f07334e0552
Create Date: 2026-05-10 13:00:08.055497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c5383fb65c4'
down_revision: Union[str, Sequence[str], None] = '7f07334e0552'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('mains', sa.Column('left_over_qty', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('mains', 'left_over_qty')

