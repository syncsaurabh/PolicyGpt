"""add scheme_id to saved_policies and make policy_id nullable

Revision ID: 0010_saved_policies_scheme_id
Revises: 0009_application_reviewer_fields
Create Date: 2026-10-09 17:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0010_saved_policies_scheme_id'
down_revision: Union[str, None] = '0009_application_reviewer_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('saved_policies', schema=None) as batch_op:
        # 1. Add scheme_id column as nullable
        batch_op.add_column(sa.Column('scheme_id', sa.Integer(), nullable=True))
        
        # 2. Make policy_id nullable to support bookmarks that reference only schemes
        batch_op.alter_column('policy_id', existing_type=sa.Integer(), nullable=True)
        
        # 3. Create foreign key constraint for scheme_id -> schemes.id
        batch_op.create_foreign_key(
            'fk_saved_policies_scheme_id_schemes',
            'schemes',
            ['scheme_id'], ['id'],
            ondelete='CASCADE'
        )
        
        # 4. Create index on scheme_id
        batch_op.create_index(op.f('ix_saved_policies_scheme_id'), ['scheme_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('saved_policies', schema=None) as batch_op:
        batch_op.drop_index(op.f('ix_saved_policies_scheme_id'))
        batch_op.drop_constraint('fk_saved_policies_scheme_id_schemes', type_='foreignkey')
        batch_op.alter_column('policy_id', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('scheme_id')

