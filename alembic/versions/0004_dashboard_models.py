"""dashboard_models
 
Revision ID: 0004_dashboard_models
Revises: 0003_milestone3
Create Date: 2026-09-23 16:15:00.000000
 
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
 
 
# revision identifiers, used by Alembic.
revision: str = '0004_dashboard_models'
down_revision: Union[str, None] = '0003_milestone3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
 
 
def upgrade() -> None:
    # --- 1. Saved Policies Table ---
    op.create_table(
        'saved_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('policy_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saved_policies_id'), 'saved_policies', ['id'], unique=False)
    op.create_index(op.f('ix_saved_policies_user_id'), 'saved_policies', ['user_id'], unique=False)
    op.create_index(op.f('ix_saved_policies_policy_id'), 'saved_policies', ['policy_id'], unique=False)

    # --- 2. Scheme Applications Table ---
    op.create_table(
        'scheme_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('scheme_id', sa.Integer(), nullable=False),
        sa.Column('application_number', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='SUBMITTED'),
        sa.Column('details_json', sa.Text(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheme_applications_id'), 'scheme_applications', ['id'], unique=False)
    op.create_index(op.f('ix_scheme_applications_user_id'), 'scheme_applications', ['user_id'], unique=False)
    op.create_index(op.f('ix_scheme_applications_scheme_id'), 'scheme_applications', ['scheme_id'], unique=False)
    op.create_index(op.f('ix_scheme_applications_application_number'), 'scheme_applications', ['application_number'], unique=True)
    op.create_index(op.f('ix_scheme_applications_status'), 'scheme_applications', ['status'], unique=False)


def downgrade() -> None:
    # --- Scheme Applications Downgrade ---
    op.drop_index(op.f('ix_scheme_applications_status'), table_name='scheme_applications')
    op.drop_index(op.f('ix_scheme_applications_application_number'), table_name='scheme_applications')
    op.drop_index(op.f('ix_scheme_applications_scheme_id'), table_name='scheme_applications')
    op.drop_index(op.f('ix_scheme_applications_user_id'), table_name='scheme_applications')
    op.drop_index(op.f('ix_scheme_applications_id'), table_name='scheme_applications')
    op.drop_table('scheme_applications')

    # --- Saved Policies Downgrade ---
    op.drop_index(op.f('ix_saved_policies_policy_id'), table_name='saved_policies')
    op.drop_index(op.f('ix_saved_policies_user_id'), table_name='saved_policies')
    op.drop_index(op.f('ix_saved_policies_id'), table_name='saved_policies')
    op.drop_table('saved_policies')
