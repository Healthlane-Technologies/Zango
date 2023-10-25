"""
first_migration

Revision ID: e5f6169a26d8
Revises: 
Create Date: 2023-07-28 09:08:40.558411
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6169a26d8'
down_revision = None
branch_labels = None
depends_on = None


   
from sqlalchemy.dialects.postgresql import ENUM


def upgrade():
    # create new tables
    op.create_table(
        'doctors',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('specialization', sa.String(50), nullable=False),
        sa.Column('phone', sa.String(15), nullable=False),
        sa.Column('email', sa.String(50), nullable=False),
        schema='tenant3'
    )
    
    gender_enum = ENUM('male', 'female', 'other', name='gender_enum', create_type=False)

    op.create_table(
        'patients',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('age', sa.Integer, nullable=False),
        gender_enum.create(op.get_bind(), checkfirst=False),
        sa.Column('phone', sa.String(15), nullable=False),
        sa.Column('email', sa.String(50), nullable=False),
        sa.Column('address', sa.String(200), nullable=False),
        sa.Column('doctor_id', sa.Integer, sa.ForeignKey('doctors.id')),
        schema='tenant3'
    )


def downgrade():
    # drop tables
    op.drop_table('patients', schema='tenant3')
    op.drop_table('doctors', schema='tenant3')
