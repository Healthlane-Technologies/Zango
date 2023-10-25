"""
added_instances

Revision ID: 2db4734de108
Revises: 8cb33102d969
Create Date: 2023-07-28 11:51:48.371241
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2db4734de108'
down_revision = '8cb33102d969'
branch_labels = None
depends_on = None


def upgrade():
    # create instances table
    op.create_table(
        'instances',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('number', sa.Integer, nullable=False),
        sa.Column('date', sa.DateTime, nullable=False),
        schema='tenant3'
    )

    # create patient_instance association table
    op.create_table(
        'patient_instance',
        sa.Column('patient_id', sa.Integer, sa.ForeignKey('patients.id')),
        sa.Column('instance_id', sa.Integer, sa.ForeignKey('instances.id')),
        schema='tenant3'
    )


def downgrade() -> None:
    op.drop_table('patient_instance', schema='tenant3')
    op.drop_table('instances', schema='tenant3')
