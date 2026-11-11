"""Add user_id to notes

Revision ID: b7d2e4f6a801
Revises: 96b0b4affee0
Create Date: 2026-11-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7d2e4f6a801'
down_revision = '96b0b4affee0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('notes') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_notes_user_id_user', 'user', ['user_id'], ['id']
        )


def downgrade():
    with op.batch_alter_table('notes') as batch_op:
        batch_op.drop_constraint('fk_notes_user_id_user', type_='foreignkey')
        batch_op.drop_column('user_id')
