"""ai_assistant_tables

Revision ID: 0006_ai_assistant_tables
Revises: 0005_notification_enhancements
Create Date: 2026-09-29 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006_ai_assistant_tables'
down_revision: Union[str, None] = '0005_notification_enhancements'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create assistant_conversations table
    op.create_table(
        'assistant_conversations',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False, server_default='New Conversation'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_assistant_conversations_user_id'), 'assistant_conversations', ['user_id'], unique=False)

    # 2. Create assistant_messages table
    op.create_table(
        'assistant_messages',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('assistant_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources_json', sa.Text(), nullable=True),
        sa.Column('intent', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_assistant_messages_id'), 'assistant_messages', ['id'], unique=False)
    op.create_index(op.f('ix_assistant_messages_conversation_id'), 'assistant_messages', ['conversation_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_assistant_messages_conversation_id'), table_name='assistant_messages')
    op.drop_index(op.f('ix_assistant_messages_id'), table_name='assistant_messages')
    op.drop_table('assistant_messages')

    op.drop_index(op.f('ix_assistant_conversations_user_id'), table_name='assistant_conversations')
    op.drop_table('assistant_conversations')
