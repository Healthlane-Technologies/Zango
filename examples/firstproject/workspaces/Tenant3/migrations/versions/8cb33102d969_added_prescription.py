"""
added_prescription

Revision ID: 8cb33102d969
Revises: e5f6169a26d8
Create Date: 2023-07-28 11:21:26.223979
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8cb33102d969'
down_revision = 'e5f6169a26d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'prescriptions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('patient_id', sa.Integer, sa.ForeignKey('patients.id')),
        sa.Column('doctor_id', sa.Integer, sa.ForeignKey('doctors.id')),
        sa.Column('medicine_name', sa.String(100), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('instructions', sa.String(500), nullable=False),
        sa.Column('date_prescribed', sa.DateTime, nullable=False),
        schema='tenant3'
    )


def downgrade() -> None:
    op.drop_table('prescriptions', schema='tenant3')
