"""email_otp_verification

Revision ID: 0008_email_otp_verification
Revises: 0007_user_profile_fields
Create Date: 2026-10-06 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0008_email_otp_verification'
down_revision: Union[str, None] = '0007_user_profile_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_verified column to users table
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), server_default='true', nullable=False))

    # Create email_otps table
    op.create_table(
        'email_otps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('otp_hash', sa.String(length=255), nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_used', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_otps_id'), 'email_otps', ['id'], unique=False)
    op.create_index(op.f('ix_email_otps_email'), 'email_otps', ['email'], unique=False)
    op.create_index(op.f('ix_email_otps_user_id'), 'email_otps', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_email_otps_user_id'), table_name='email_otps')
    op.drop_index(op.f('ix_email_otps_email'), table_name='email_otps')
    op.drop_index(op.f('ix_email_otps_id'), table_name='email_otps')
    op.drop_table('email_otps')
    op.drop_column('users', 'is_verified')
