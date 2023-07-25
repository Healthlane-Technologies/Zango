"""
added testmodel

Revision ID: bfe684020053
Revises: 
Create Date: 2023-07-25 13:06:17.462459
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bfe684020053'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'MyUsers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False, unique=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='tenant3'
    )


def downgrade():
    op.drop_table('MyUsers', schema='tenant3')

