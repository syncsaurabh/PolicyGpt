"""milestone3_schema

Revision ID: 0003_milestone3
Revises: 0002_milestone2
Create Date: 2026-09-15 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_milestone3'
down_revision: Union[str, None] = '0002_milestone2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 1. Upgrade Notifications Table ---
    op.add_column('notifications', sa.Column('notification_type', sa.String(length=50), nullable=False, server_default='GENERAL'))
    op.add_column('notifications', sa.Column('channel', sa.String(length=50), nullable=False, server_default='IN_APP'))
    op.add_column('notifications', sa.Column('status', sa.String(length=50), nullable=False, server_default='SENT'))
    op.add_column('notifications', sa.Column('entity_type', sa.String(length=100), nullable=True))
    op.add_column('notifications', sa.Column('entity_id', sa.String(length=100), nullable=True))
    op.add_column('notifications', sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True))

    op.create_index(op.f('ix_notifications_notification_type'), 'notifications', ['notification_type'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)

    # --- 2. Create Notification Preferences Table ---
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('sms_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('in_app_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('policy_alerts', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('scheme_updates', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('deadline_reminders', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('system_alerts', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_preferences_id'), 'notification_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=True)

    # --- 3. Upgrade Feedback Table ---
    op.add_column('feedback', sa.Column('feedback_type', sa.String(length=50), nullable=False, server_default='FEEDBACK'))
    op.add_column('feedback', sa.Column('category', sa.String(length=100), nullable=True))
    op.add_column('feedback', sa.Column('status', sa.String(length=50), nullable=False, server_default='SUBMITTED'))
    op.add_column('feedback', sa.Column('priority', sa.String(length=50), nullable=False, server_default='MEDIUM'))
    op.add_column('feedback', sa.Column('admin_response', sa.Text(), nullable=True))
    op.add_column('feedback', sa.Column('resolved_by_id', sa.Integer(), nullable=True))
    op.add_column('feedback', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('feedback', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    op.create_foreign_key('fk_feedback_resolved_by', 'feedback', 'users', ['resolved_by_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_feedback_feedback_type'), 'feedback', ['feedback_type'], unique=False)
    op.create_index(op.f('ix_feedback_category'), 'feedback', ['category'], unique=False)
    op.create_index(op.f('ix_feedback_status'), 'feedback', ['status'], unique=False)
    op.create_index(op.f('ix_feedback_priority'), 'feedback', ['priority'], unique=False)

    # --- 4. Create FAQs Table ---
    op.create_table(
        'faqs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question', sa.String(length=500), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_faqs_id'), 'faqs', ['id'], unique=False)
    op.create_index(op.f('ix_faqs_question'), 'faqs', ['question'], unique=False)
    op.create_index(op.f('ix_faqs_category'), 'faqs', ['category'], unique=False)
    op.create_index(op.f('ix_faqs_is_active'), 'faqs', ['is_active'], unique=False)

    # --- 5. Create User Activities Table ---
    op.create_table(
        'user_activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_activities_id'), 'user_activities', ['id'], unique=False)
    op.create_index(op.f('ix_user_activities_user_id'), 'user_activities', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_activities_event_type'), 'user_activities', ['event_type'], unique=False)
    op.create_index(op.f('ix_user_activities_resource_type'), 'user_activities', ['resource_type'], unique=False)
    op.create_index(op.f('ix_user_activities_created_at'), 'user_activities', ['created_at'], unique=False)

    # --- 6. Upgrade Reports Table ---
    op.add_column('reports', sa.Column('file_format', sa.String(length=50), nullable=True))
    op.add_column('reports', sa.Column('parameters_json', sa.Text(), nullable=True))
    op.add_column('reports', sa.Column('status', sa.String(length=50), nullable=False, server_default='COMPLETED'))
    op.add_column('reports', sa.Column('record_count', sa.Integer(), nullable=False, server_default='0'))

    op.create_index(op.f('ix_reports_report_type'), 'reports', ['report_type'], unique=False)
    op.create_index(op.f('ix_reports_created_at'), 'reports', ['created_at'], unique=False)


def downgrade() -> None:
    # --- 6. Downgrade Reports Table ---
    op.drop_index(op.f('ix_reports_created_at'), table_name='reports')
    op.drop_index(op.f('ix_reports_report_type'), table_name='reports')
    op.drop_column('reports', 'record_count')
    op.drop_column('reports', 'status')
    op.drop_column('reports', 'parameters_json')
    op.drop_column('reports', 'file_format')

    # --- 5. Downgrade User Activities Table ---
    op.drop_index(op.f('ix_user_activities_created_at'), table_name='user_activities')
    op.drop_index(op.f('ix_user_activities_resource_type'), table_name='user_activities')
    op.drop_index(op.f('ix_user_activities_event_type'), table_name='user_activities')
    op.drop_index(op.f('ix_user_activities_user_id'), table_name='user_activities')
    op.drop_index(op.f('ix_user_activities_id'), table_name='user_activities')
    op.drop_table('user_activities')

    # --- 4. Downgrade FAQs Table ---
    op.drop_index(op.f('ix_faqs_is_active'), table_name='faqs')
    op.drop_index(op.f('ix_faqs_category'), table_name='faqs')
    op.drop_index(op.f('ix_faqs_question'), table_name='faqs')
    op.drop_index(op.f('ix_faqs_id'), table_name='faqs')
    op.drop_table('faqs')

    # --- 3. Downgrade Feedback Table ---
    op.drop_index(op.f('ix_feedback_priority'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_status'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_category'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_feedback_type'), table_name='feedback')
    op.drop_constraint('fk_feedback_resolved_by', 'feedback', type_='foreignkey')
    op.drop_column('feedback', 'updated_at')
    op.drop_column('feedback', 'resolved_at')
    op.drop_column('feedback', 'resolved_by_id')
    op.drop_column('feedback', 'admin_response')
    op.drop_column('feedback', 'priority')
    op.drop_column('feedback', 'status')
    op.drop_column('feedback', 'category')
    op.drop_column('feedback', 'feedback_type')

    # --- 2. Downgrade Notification Preferences Table ---
    op.drop_index(op.f('ix_notification_preferences_user_id'), table_name='notification_preferences')
    op.drop_index(op.f('ix_notification_preferences_id'), table_name='notification_preferences')
    op.drop_table('notification_preferences')

    # --- 1. Downgrade Notifications Table ---
    op.drop_index(op.f('ix_notifications_is_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_notification_type'), table_name='notifications')
    op.drop_column('notifications', 'sent_at')
    op.drop_column('notifications', 'entity_id')
    op.drop_column('notifications', 'entity_type')
    op.drop_column('notifications', 'status')
    op.drop_column('notifications', 'channel')
    op.drop_column('notifications', 'notification_type')
