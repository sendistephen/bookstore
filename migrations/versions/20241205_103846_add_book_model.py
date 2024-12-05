"""Add Book model

Revision ID: 1d9c625bb30e
Revises: 97cd3c20cc92
Create Date: 2024-12-05 10:38:46.718561+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d9c625bb30e'
down_revision: Union[str, None] = '97cd3c20cc92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
