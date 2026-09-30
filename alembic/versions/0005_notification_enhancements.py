"""notification_enhancements

Revision ID: 0005_notification_enhancements
Revises: 0004_dashboard_models
Create Date: 2026-09-25 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005_notification_enhancements'
down_revision: Union[str, None] = '0004_dashboard_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add read_at and scheduled_at to notifications table
    op.add_column('notifications', sa.Column('read_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('notifications', sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True))

    # 2. Add application_updates to notification_preferences table
    op.add_column('notification_preferences', sa.Column('application_updates', sa.Boolean(), nullable=False, server_default=sa.text('true')))

    # 3. Add phone_number to users table
    op.add_column('users', sa.Column('phone_number', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # 3. Drop phone_number from users
    op.drop_column('users', 'phone_number')

    # 2. Drop application_updates from notification_preferences
    op.drop_column('notification_preferences', 'application_updates')

    # 1. Drop scheduled_at and read_at from notifications
    op.drop_column('notifications', 'scheduled_at')
    op.drop_column('notifications', 'read_at')
