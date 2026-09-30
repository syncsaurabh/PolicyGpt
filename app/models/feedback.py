from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class FeedbackType(str, Enum):
    FEEDBACK = "FEEDBACK"
    ISSUE = "ISSUE"
    SUPPORT = "SUPPORT"
    INQUIRY = "INQUIRY"
    SUGGESTION = "SUGGESTION"
    COMPLAINT = "COMPLAINT"


class FeedbackStatus(str, Enum):
    OPEN = "OPEN"
    SUBMITTED = "SUBMITTED"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class FeedbackPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Feedback(Base):
    """Citizen feedback, support tickets, and issue reporting model."""
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    feedback_type: Mapped[str] = mapped_column(String(50), default=FeedbackType.FEEDBACK.value, nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=FeedbackStatus.SUBMITTED.value, nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(50), default=FeedbackPriority.MEDIUM.value, nullable=False, index=True)
    admin_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    resolver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[resolved_by_id])

    def __repr__(self) -> str:
        return f"<Feedback id={self.id} type={self.feedback_type} status={self.status} subject='{self.subject}'>"
