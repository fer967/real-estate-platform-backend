"""add messenger_id to contacts

Revision ID: 3cbd6823d906
Revises: 81dc6d11ca92
Create Date: 2026-05-05 15:19:19.110973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3cbd6823d906'
down_revision: Union[str, Sequence[str], None] = '81dc6d11ca92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
