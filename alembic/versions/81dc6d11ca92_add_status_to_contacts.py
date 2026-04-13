"""add status to contacts

Revision ID: 81dc6d11ca92
Revises: e2e2f06f8956
Create Date: 2026-04-12 22:06:41.391231

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81dc6d11ca92'
down_revision: Union[str, Sequence[str], None] = 'e2e2f06f8956'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
