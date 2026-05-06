"""create_table_transport

Revision ID: 87dae7885e98
Revises: 26c44d3f452f
Create Date: 2026-05-06 10:26:46.001998

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87dae7885e98'
down_revision: Union[str, Sequence[str], None] = '26c44d3f452f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'transports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('structure_1', sa.String(), nullable=True),
        sa.Column('structure_2', sa.String(), nullable=True),
        sa.Column('raw_labels', sa.String(), nullable=True),
        sa.Column('mark_name', sa.String(), nullable=True),
        sa.Column('t_qty', sa.Float(), nullable=True),
        sa.Column('t_weight', sa.Float(), nullable=True),
        sa.Column('t_date', sa.Date(), nullable=True),
        sa.Column('t_status', sa.String(), nullable=True),
        sa.Column('proce_qty', sa.Integer(), nullable=True),
        sa.Column('order_no', sa.String(), nullable=True),
        sa.Column('key', sa.String(), nullable=True),
        sa.Column('area', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_transports_id'), 'transports', ['id'], unique=False)
    op.create_foreign_key('fk_transports_created_by_users', 'transports', 'users', ['created_by'], ['id'],
                          ondelete='SET NULL')


def downgrade() -> None:
    op.drop_table('transports')