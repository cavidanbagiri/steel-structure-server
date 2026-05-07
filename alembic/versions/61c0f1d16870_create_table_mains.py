"""create_table_mains

Revision ID: 61c0f1d16870
Revises: 87dae7885e98
Create Date: 2026-05-07 16:27:22.638386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61c0f1d16870'
down_revision: Union[str, Sequence[str], None] = '87dae7885e98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'mains',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('area', sa.String(), nullable=True),
        sa.Column('zone', sa.String(), nullable=True),
        sa.Column('key', sa.String(), nullable=True),
        sa.Column('row_labels', sa.String(), nullable=True),
        sa.Column('item', sa.String(), nullable=True),
        sa.Column('p_s', sa.String(), nullable=True),
        sa.Column('qty', sa.Float(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('section', sa.String(), nullable=True),
        sa.Column('length', sa.Float(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('weight_total', sa.Float(), nullable=True),
        sa.Column('dwgn', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mains_id', 'mains', ['id'])

def downgrade() -> None:
    op.drop_index('ix_mains_id', table_name='mains')
    op.drop_table('mains')
