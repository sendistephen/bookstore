"""Add category schema

Revision ID: 4a09f348aeba
Revises: 51bc732f945c
Create Date: 2024-12-02 15:51:18.737145

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a09f348aeba'
down_revision = '51bc732f945c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('book_categories',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=32), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('book_categories')
    # ### end Alembic commands ###
