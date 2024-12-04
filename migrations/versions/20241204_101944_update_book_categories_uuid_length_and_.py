"""Update book_categories UUID length and add unique constraint

Revision ID: 97cd3c20cc92
Revises: 5fcc1551da00
Create Date: 2024-12-04 10:19:44.165296+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97cd3c20cc92'
down_revision: Union[str, None] = '5fcc1551da00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter the id column to increase length to 36 characters
    op.alter_column('book_categories', 'id', 
                    type_=sa.String(36),
                    existing_type=sa.String(32))
    
    # Add unique constraint to the name column
    op.create_unique_constraint('uq_book_categories_name', 
                                'book_categories', 
                                ['name'])


def downgrade() -> None:
    # Remove unique constraint from the name column
    op.drop_constraint('uq_book_categories_name', 
                       'book_categories', 
                       type_='unique')
    
    # Revert the id column length back to 32 characters
    op.alter_column('book_categories', 'id', 
                    type_=sa.String(32),
                    existing_type=sa.String(36))
