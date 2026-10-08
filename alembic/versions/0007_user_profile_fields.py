"""user_profile_fields

Revision ID: 0007_user_profile_fields
Revises: 0006_ai_assistant_tables
Create Date: 2026-10-05 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007_user_profile_fields'
down_revision: Union[str, None] = '0006_ai_assistant_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('state', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('pincode', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'pincode')
    op.drop_column('users', 'address')
    op.drop_column('users', 'state')
    op.drop_column('users', 'age')
