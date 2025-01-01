"""Add file upload to book model

Revision ID: 8509e157f670
Revises: 9aaca4b8f74c
Create Date: 2024-12-31 09:47:26.712629+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8509e157f670'
down_revision: Union[str, None] = '9aaca4b8f74c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('books', sa.Column('front_cover_url', sa.String(length=500), nullable=True))
    op.add_column('books', sa.Column('front_cover_public_id', sa.String(length=255), nullable=True))
    op.add_column('books', sa.Column('back_cover_url', sa.String(length=500), nullable=True))
    op.add_column('books', sa.Column('back_cover_public_id', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('books', 'back_cover_public_id')
    op.drop_column('books', 'back_cover_url')
    op.drop_column('books', 'front_cover_public_id')
    op.drop_column('books', 'front_cover_url')
    # ### end Alembic commands ###