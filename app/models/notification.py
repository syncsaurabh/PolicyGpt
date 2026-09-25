from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class NotificationType(str, Enum):
    NEW_POLICY = "NEW_POLICY"
    POLICY_CREATED = "POLICY_CREATED"
    POLICY_UPDATED = "POLICY_UPDATED"
    POLICY_APPROVED = "POLICY_APPROVED"
    POLICY_REJECTED = "POLICY_REJECTED"
    NEW_SCHEME = "NEW_SCHEME"
    SCHEME_CREATED = "SCHEME_CREATED"
    SCHEME_UPDATED = "SCHEME_UPDATED"
    SCHEME_UPDATE = "SCHEME_UPDATE"
    SCHEME_DEADLINE = "SCHEME_DEADLINE"
    DEADLINE_REMINDER = "DEADLINE_REMINDER"
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED"
    APPLICATION_STATUS_CHANGED = "APPLICATION_STATUS_CHANGED"
    APPLICATION_APPROVED = "APPLICATION_APPROVED"
    APPLICATION_REJECTED = "APPLICATION_REJECTED"
    APPLICATION_UPDATE = "APPLICATION_UPDATE"
    APPLICATION_UPDATED = "APPLICATION_UPDATED"
    ELIGIBILITY_MATCH = "ELIGIBILITY_MATCH"
    SYSTEM_ANNOUNCEMENT = "SYSTEM_ANNOUNCEMENT"
    SYSTEM_ALERT = "SYSTEM_ALERT"
    FEEDBACK_RESPONSE = "FEEDBACK_RESPONSE"
    GENERAL = "GENERAL"


class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    READ = "READ"


class Notification(Base):
    """Notification model supporting in-app, email, SMS alerts and status tracking."""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), default=NotificationType.GENERAL.value, nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(50), default=NotificationChannel.IN_APP.value, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=NotificationStatus.SENT.value, nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} title='{self.title}' is_read={self.is_read}>"


class NotificationPreference(Base):
    """User notification channel and topic delivery preferences."""
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    policy_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scheme_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deadline_reminders: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    application_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    system_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<NotificationPreference user_id={self.user_id}>"
