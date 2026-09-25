"""milestone2_schema

Revision ID: 0002_milestone2
Revises: 0001_initial
Create Date: 2026-09-07 13:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_milestone2'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 1. Policies Table Upgrades ---
    op.add_column('policies', sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'))
    op.add_column('policies', sa.Column('ministry', sa.String(length=200), nullable=True))
    op.add_column('policies', sa.Column('state', sa.String(length=100), nullable=True))
    op.add_column('policies', sa.Column('sector', sa.String(length=100), nullable=True))
    op.add_column('policies', sa.Column('publication_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('policies', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('policies', sa.Column('created_by_id', sa.Integer(), nullable=True))
    op.add_column('policies', sa.Column('approved_by_id', sa.Integer(), nullable=True))

    op.create_foreign_key('fk_policies_created_by', 'policies', 'users', ['created_by_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_policies_approved_by', 'policies', 'users', ['approved_by_id'], ['id'], ondelete='SET NULL')

    op.create_index(op.f('ix_policies_status'), 'policies', ['status'], unique=False)
    op.create_index(op.f('ix_policies_department'), 'policies', ['department'], unique=False)
    op.create_index(op.f('ix_policies_ministry'), 'policies', ['ministry'], unique=False)
    op.create_index(op.f('ix_policies_state'), 'policies', ['state'], unique=False)
    op.create_index(op.f('ix_policies_sector'), 'policies', ['sector'], unique=False)

    # --- 2. Schemes Table Upgrades ---
    op.add_column('schemes', sa.Column('category', sa.String(length=100), nullable=True))
    op.add_column('schemes', sa.Column('department', sa.String(length=150), nullable=True))
    op.add_column('schemes', sa.Column('ministry', sa.String(length=200), nullable=True))
    op.add_column('schemes', sa.Column('state', sa.String(length=100), nullable=True))
    op.add_column('schemes', sa.Column('sector', sa.String(length=100), nullable=True))
    op.add_column('schemes', sa.Column('application_process', sa.Text(), nullable=True))
    op.add_column('schemes', sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'))
    op.add_column('schemes', sa.Column('publication_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('schemes', sa.Column('created_by_id', sa.Integer(), nullable=True))

    op.create_foreign_key('fk_schemes_created_by', 'schemes', 'users', ['created_by_id'], ['id'], ondelete='SET NULL')

    op.create_index(op.f('ix_schemes_category'), 'schemes', ['category'], unique=False)
    op.create_index(op.f('ix_schemes_department'), 'schemes', ['department'], unique=False)
    op.create_index(op.f('ix_schemes_ministry'), 'schemes', ['ministry'], unique=False)
    op.create_index(op.f('ix_schemes_state'), 'schemes', ['state'], unique=False)
    op.create_index(op.f('ix_schemes_sector'), 'schemes', ['sector'], unique=False)
    op.create_index(op.f('ix_schemes_status'), 'schemes', ['status'], unique=False)


def downgrade() -> None:
    # --- Schemes Downgrade ---
    op.drop_index(op.f('ix_schemes_status'), table_name='schemes')
    op.drop_index(op.f('ix_schemes_sector'), table_name='schemes')
    op.drop_index(op.f('ix_schemes_state'), table_name='schemes')
    op.drop_index(op.f('ix_schemes_ministry'), table_name='schemes')
    op.drop_index(op.f('ix_schemes_department'), table_name='schemes')
    op.drop_index(op.f('ix_schemes_category'), table_name='schemes')
    op.drop_constraint('fk_schemes_created_by', 'schemes', type_='foreignkey')

    op.drop_column('schemes', 'created_by_id')
    op.drop_column('schemes', 'publication_date')
    op.drop_column('schemes', 'status')
    op.drop_column('schemes', 'application_process')
    op.drop_column('schemes', 'sector')
    op.drop_column('schemes', 'state')
    op.drop_column('schemes', 'ministry')
    op.drop_column('schemes', 'department')
    op.drop_column('schemes', 'category')

    # --- Policies Downgrade ---
    op.drop_index(op.f('ix_policies_sector'), table_name='policies')
    op.drop_index(op.f('ix_policies_state'), table_name='policies')
    op.drop_index(op.f('ix_policies_ministry'), table_name='policies')
    op.drop_index(op.f('ix_policies_department'), table_name='policies')
    op.drop_index(op.f('ix_policies_status'), table_name='policies')
    op.drop_constraint('fk_policies_approved_by', 'policies', type_='foreignkey')
    op.drop_constraint('fk_policies_created_by', 'policies', type_='foreignkey')

    op.drop_column('policies', 'approved_by_id')
    op.drop_column('policies', 'created_by_id')
    op.drop_column('policies', 'rejection_reason')
    op.drop_column('policies', 'publication_date')
    op.drop_column('policies', 'sector')
    op.drop_column('policies', 'state')
    op.drop_column('policies', 'ministry')
    op.drop_column('policies', 'status')
