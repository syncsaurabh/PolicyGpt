"""Base database module that registers all models for Alembic migrations."""
from app.db.database import Base
from app.models.user import User, UserRole
from app.models.policy import Policy
from app.models.scheme import Scheme
from app.models.eligibility import EligibilityRule
from app.models.notification import Notification
from app.models.feedback import Feedback
from app.models.report import Report
from app.models.audit_log import AuditLog
from app.models.search_history import SearchHistory

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Policy",
    "Scheme",
    "EligibilityRule",
    "Notification",
    "Feedback",
    "Report",
    "AuditLog",
    "SearchHistory",
]
