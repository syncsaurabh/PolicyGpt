"""application_reviewer_fields

Revision ID: 0009_application_reviewer_fields
Revises: 0008_email_otp_verification
Create Date: 2026-10-07 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0009_application_reviewer_fields'
down_revision: Union[str, None] = '0008_email_otp_verification'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scheme_applications', sa.Column('reviewed_by_id', sa.Integer(), nullable=True))
    op.add_column('scheme_applications', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        'fk_scheme_applications_reviewed_by_id_users',
        'scheme_applications', 'users',
        ['reviewed_by_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index(op.f('ix_scheme_applications_reviewed_by_id'), 'scheme_applications', ['reviewed_by_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_scheme_applications_reviewed_by_id'), table_name='scheme_applications')
    op.drop_constraint('fk_scheme_applications_reviewed_by_id_users', 'scheme_applications', type_='foreignkey')
    op.drop_column('scheme_applications', 'reviewed_at')
    op.drop_column('scheme_applications', 'reviewed_by_id')
