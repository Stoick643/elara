"""Add onboarding and pro_mode columns to users table

Revision ID: bbe80a3f3d7f
Revises: 
Create Date: 2025-09-14 11:30:44.172087

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bbe80a3f3d7f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('onboarding_completed', sa.Boolean(), nullable=True, default=False))
        batch_op.add_column(sa.Column('onboarding_step', sa.Integer(), nullable=True, default=0))
        batch_op.add_column(sa.Column('is_pro_mode', sa.Boolean(), nullable=True, default=False))


def downgrade():
    # Remove the columns if we need to rollback
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_pro_mode')
        batch_op.drop_column('onboarding_step')
        batch_op.drop_column('onboarding_completed')
