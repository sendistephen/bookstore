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
    
    # Add unique constraint to the name column, skipping if it already exists
    with op.get_context().autocommit_block():
        try:
            op.create_unique_constraint('uq_book_categories_name', 
                                        'book_categories', 
                                        ['name'])
        except sa.exc.ProgrammingError:
            # Constraint already exists, so we can safely ignore this error
            pass


def downgrade() -> None:
    # Remove unique constraint from the name column
    with op.get_context().autocommit_block():
        try:
            op.drop_constraint('uq_book_categories_name', 
                               'book_categories', 
                               type_='unique')
        except sa.exc.ProgrammingError:
            # Constraint doesn't exist, so we can safely ignore this error
            pass
    
    # Revert the id column length back to 32 characters
    op.alter_column('book_categories', 'id', 
                    type_=sa.String(32),
                    existing_type=sa.String(36))
