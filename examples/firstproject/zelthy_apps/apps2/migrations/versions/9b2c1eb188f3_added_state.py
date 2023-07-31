"""
added_state

Revision ID: 9b2c1eb188f3
Revises: fd489e0881c7
Create Date: 2023-07-28 10:13:06.046647
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b2c1eb188f3'
down_revision = 'fd489e0881c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('MyUsers', sa.Column('state', sa.String(100), nullable=True), schema='apps2')


def downgrade() -> None:
    op.drop_column('MyUsers', 'state', schema='apps2')

