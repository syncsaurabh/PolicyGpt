"""Base database module that registers all models for Alembic migrations."""
from app.db.database import Base
from app.models.user import User, UserRole
from app.models.policy import Policy, PolicyStatus, PolicyCategory
from app.models.scheme import Scheme, SchemeStatus, SchemeCategory
from app.models.eligibility import EligibilityRule
from app.models.notification import (
    Notification,
    NotificationPreference,
    NotificationType,
    NotificationChannel,
    NotificationStatus,
)
from app.models.feedback import (
    Feedback,
    FeedbackType,
    FeedbackStatus,
    FeedbackPriority,
)
from app.models.faq import FAQ
from app.models.user_activity import UserActivity
from app.models.report import Report, ReportType, ReportFormat
from app.models.audit_log import AuditLog
from app.models.search_history import SearchHistory
from app.models.saved_policy import SavedPolicy
from app.models.application import SchemeApplication, ApplicationStatus
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.otp import EmailOTP

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Policy",
    "PolicyStatus",
    "PolicyCategory",
    "Scheme",
    "SchemeStatus",
    "SchemeCategory",
    "EligibilityRule",
    "Notification",
    "NotificationPreference",
    "NotificationType",
    "NotificationChannel",
    "NotificationStatus",
    "Feedback",
    "FeedbackType",
    "FeedbackStatus",
    "FeedbackPriority",
    "FAQ",
    "UserActivity",
    "Report",
    "ReportType",
    "ReportFormat",
    "AuditLog",
    "SearchHistory",
    "SavedPolicy",
    "SchemeApplication",
    "ApplicationStatus",
    "AssistantConversation",
    "AssistantMessage",
    "EmailOTP",
]
