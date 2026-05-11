"""add_column_to_erected_createdby

Revision ID: 6e497d7dc8e4
Revises: 9c5383fb65c4
Create Date: 2026-05-10 14:55:40.189796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e497d7dc8e4'
down_revision: Union[str, Sequence[str], None] = '9c5383fb65c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('erecteds', sa.Column('created_by', sa.Integer(), nullable=True))

    # 2. Create the foreign key
    op.create_foreign_key(
        'fk_erecteds_created_by_users',
        'erecteds', 'users',
        ['created_by'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Drop the foreign key first (using its name)
    op.drop_constraint('fk_erecteds_created_by_users', 'erecteds', type_='foreignkey')

    # 2. Drop the column
    op.drop_column('erecteds', 'created_by')
