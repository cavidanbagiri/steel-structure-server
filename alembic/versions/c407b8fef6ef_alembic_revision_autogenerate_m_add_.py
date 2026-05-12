"""alembic revision --autogenerate -m add_main_id_to_transport

Revision ID: c407b8fef6ef
Revises: 49043396e724
Create Date: 2026-05-12 19:38:30.928780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c407b8fef6ef'
down_revision: Union[str, Sequence[str], None] = '49043396e724'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add the main_id column to the transports table
    op.add_column('transports', sa.Column('main_id', sa.Integer(), nullable=True))

    # 2. Create the foreign key constraint pointing to the mains table
    op.create_foreign_key(
        'fk_transports_main_id_mains',  # Constraint name
        'transports',  # Source table
        'mains',  # Target table
        ['main_id'],  # Source column(s)
        ['id'],  # Target column(s)
        ondelete='SET NULL'  # Match model behavior
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Drop the foreign key constraint first
    op.drop_constraint('fk_transports_main_id_mains', 'transports', type_='foreignkey')

    # 2. Drop the column
    op.drop_column('transports', 'main_id')