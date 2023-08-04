"""
alter_patient_extradata

Revision ID: 7d506028e9e5
Revises: 2db4734de108
Create Date: 2023-07-28 12:44:01.391373
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d506028e9e5'
down_revision = '2db4734de108'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'associated_patients',
        sa.Column('patient_id', sa.Integer, sa.ForeignKey('patients.id')),
        sa.Column('associated_patient_id', sa.Integer, sa.ForeignKey('patients.id')),
        schema='tenant3'
    )



def downgrade() -> None:
    op.drop_table('associated_patients', schema='tenant3')
