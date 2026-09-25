from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.notification import NotificationType, NotificationChannel, NotificationStatus


class NotificationPreferenceRead(BaseModel):
    id: int
    user_id: int
    email_enabled: bool
    sms_enabled: bool
    in_app_enabled: bool
    policy_alerts: bool
    scheme_updates: bool
    deadline_reminders: bool
    application_updates: bool = True
    system_alerts: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    policy_alerts: Optional[bool] = None
    scheme_updates: Optional[bool] = None
    deadline_reminders: Optional[bool] = None
    application_updates: Optional[bool] = None
    system_alerts: Optional[bool] = None


class NotificationCreate(BaseModel):
    user_id: int = Field(..., description="Target user ID")
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    notification_type: NotificationType = NotificationType.GENERAL
    channel: NotificationChannel = NotificationChannel.IN_APP
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class NotificationBroadcast(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    notification_type: NotificationType = NotificationType.SYSTEM_ALERT
    channel: NotificationChannel = NotificationChannel.IN_APP
    target_roles: Optional[List[str]] = Field(None, description="Optional target user roles; None targets all active users")


class NotificationRead(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    channel: str
    status: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationPaginationResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    unread_count: int
    results: List[NotificationRead]
