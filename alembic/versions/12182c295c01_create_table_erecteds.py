"""create_table_erecteds

Revision ID: 12182c295c01
Revises: 61c0f1d16870
Create Date: 2026-05-07 16:48:46.741843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '12182c295c01'
down_revision: Union[str, Sequence[str], None] = '61c0f1d16870'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'erecteds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('area', sa.String(), nullable=True),
        sa.Column('structure', sa.String(), nullable=True),
        sa.Column('row_labels', sa.String(), nullable=True),
        sa.Column('mark_names', sa.String(), nullable=True),
        sa.Column('e_qty', sa.Float(), nullable=True),
        sa.Column('e_weight', sa.Float(), nullable=True),
        sa.Column('daily_e_date', sa.Date(), nullable=True),
        sa.Column('proce_qty', sa.Float(), nullable=True),
        sa.Column('altitude_mark_1', sa.String(), nullable=True),
        sa.Column('axis', sa.String(), nullable=True),
        sa.Column('range', sa.String(), nullable=True),
        sa.Column('altitude_mark_2', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_erecteds_id', 'erecteds', ['id'])

def downgrade() -> None:
    op.drop_index('ix_erecteds_id', table_name='erecteds')
    op.drop_table('erecteds')
