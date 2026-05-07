"""create_table_combines

Revision ID: 7f07334e0552
Revises: 12182c295c01
Create Date: 2026-05-07 16:59:08.802175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f07334e0552'
down_revision: Union[str, Sequence[str], None] = '12182c295c01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'combine',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transport_id', sa.Integer(), nullable=True),
        sa.Column('main_id', sa.Integer(), nullable=True),
        sa.Column('erected_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_combine_id', 'combine', ['id'])

    # Create foreign key constraints
    op.create_foreign_key(
        'fk_combine_transport_id',
        'combine', 'transports',
        ['transport_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_combine_main_id',
        'combine', 'mains',
        ['main_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_combine_erected_id',
        'combine', 'erecteds',
        ['erected_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_combine_erected_id', 'combine', type_='foreignkey')
    op.drop_constraint('fk_combine_main_id', 'combine', type_='foreignkey')
    op.drop_constraint('fk_combine_transport_id', 'combine', type_='foreignkey')
    op.drop_index('ix_combine_id', table_name='combine')
    op.drop_table('combine')
