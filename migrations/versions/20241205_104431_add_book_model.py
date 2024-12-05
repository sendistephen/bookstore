"""Add Book model

Revision ID: 0b10998abd2a
Revises: 1d9c625bb30e
Create Date: 2024-12-05 10:44:31.227991+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b10998abd2a'
down_revision: Union[str, None] = '1d9c625bb30e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
