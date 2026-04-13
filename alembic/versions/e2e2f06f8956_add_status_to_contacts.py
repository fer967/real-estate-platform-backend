"""add status to contacts

Revision ID: e2e2f06f8956
Revises: 5fd3409a733a
Create Date: 2026-04-12 21:42:01.879676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2e2f06f8956'
down_revision: Union[str, Sequence[str], None] = '5fd3409a733a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('contacts', sa.Column('status', sa.String(), nullable=True))

def downgrade():
    op.drop_column('contacts', 'status')