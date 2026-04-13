"""add direction to leads

Revision ID: 5fd3409a733a
Revises: 2445ab25f9a9
Create Date: 2026-04-12 16:10:25.798202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5fd3409a733a'
down_revision: Union[str, Sequence[str], None] = '2445ab25f9a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('leads', sa.Column('direction', sa.String(), nullable=True))

def downgrade():
    op.drop_column('leads', 'direction')
