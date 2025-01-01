"""Update order by adding billing information

Revision ID: 0862a0bdd11b
Revises: 68489e6fc274
Create Date: 2025-01-01 16:16:32.585038+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0862a0bdd11b'
down_revision: Union[str, None] = '68489e6fc274'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('orders', 'billing_name',
               existing_type=sa.VARCHAR(length=100),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'billing_email',
               existing_type=sa.VARCHAR(length=100),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'billing_phone',
               existing_type=sa.VARCHAR(length=20),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'billing_street',
               existing_type=sa.VARCHAR(length=200),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'billing_city',
               existing_type=sa.VARCHAR(length=100),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'billing_state',
               existing_type=sa.VARCHAR(length=100),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'billing_postal_code',
               existing_type=sa.VARCHAR(length=20),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'billing_country',
               existing_type=sa.VARCHAR(length=100),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'shipping_name',
               existing_type=sa.VARCHAR(length=100),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'shipping_email',
               existing_type=sa.VARCHAR(length=100),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'shipping_phone',
               existing_type=sa.VARCHAR(length=20),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'shipping_street',
               existing_type=sa.VARCHAR(length=200),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'shipping_city',
               existing_type=sa.VARCHAR(length=100),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'shipping_state',
               existing_type=sa.VARCHAR(length=100),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'shipping_postal_code',
               existing_type=sa.VARCHAR(length=20),
               server_default=None,
               existing_nullable=True)
    op.alter_column('orders', 'shipping_country',
               existing_type=sa.VARCHAR(length=100),
               server_default=None,
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('orders', 'shipping_country',
               existing_type=sa.VARCHAR(length=100),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'shipping_postal_code',
               existing_type=sa.VARCHAR(length=20),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'shipping_state',
               existing_type=sa.VARCHAR(length=100),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'shipping_city',
               existing_type=sa.VARCHAR(length=100),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'shipping_street',
               existing_type=sa.VARCHAR(length=200),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'shipping_phone',
               existing_type=sa.VARCHAR(length=20),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'shipping_email',
               existing_type=sa.VARCHAR(length=100),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'shipping_name',
               existing_type=sa.VARCHAR(length=100),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'billing_country',
               existing_type=sa.VARCHAR(length=100),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'billing_postal_code',
               existing_type=sa.VARCHAR(length=20),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'billing_state',
               existing_type=sa.VARCHAR(length=100),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'billing_city',
               existing_type=sa.VARCHAR(length=100),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'billing_street',
               existing_type=sa.VARCHAR(length=200),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'billing_phone',
               existing_type=sa.VARCHAR(length=20),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'billing_email',
               existing_type=sa.VARCHAR(length=100),
               server_default=sa.text("''::character varying"),
               existing_nullable=True)
    op.alter_column('orders', 'billing_name',
               existing_type=sa.VARCHAR(length=100),
               server_default=sa.text("'Unknown'::character varying"),
               existing_nullable=True)
    # ### end Alembic commands ###
