"""Add subtitle to notes

Revision ID: 98c7accc0b3d
Revises: 99d9908b6a4b
Create Date: 2026-09-05 11:01:01.834169

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98c7accc0b3d'
down_revision = '99d9908b6a4b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'notes',
        sa.Column('subtitle', sa.String(length=200), nullable=True)
    )

def downgrade():
    op.drop_column('notes', 'subtitle')
