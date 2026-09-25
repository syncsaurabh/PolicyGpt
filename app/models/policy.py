from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.scheme import Scheme
    from app.models.user import User


class PolicyStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class PolicyCategory(str, Enum):
    EDUCATION = "Education"
    HEALTHCARE = "Healthcare"
    AGRICULTURE = "Agriculture"
    EMPLOYMENT = "Employment"
    FINANCE = "Finance"
    WOMEN_CHILD_WELFARE = "Women & Child Welfare"
    HOUSING = "Housing"
    ENVIRONMENT = "Environment"
    DIGITAL_GOVERNANCE = "Digital Governance"
    INFRASTRUCTURE = "Infrastructure"


class Policy(Base):
    """Policy model supporting full lifecycle management and approval workflows."""
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(150), nullable=True, index=True)
    ministry: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=PolicyStatus.DRAFT.value, index=True)
    publication_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    schemes: Mapped[List["Scheme"]] = relationship("Scheme", back_populates="policy", cascade="all, delete-orphan")
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
    approved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_id])

    def __repr__(self) -> str:
        return f"<Policy id={self.id} title='{self.title}' status={self.status}>"
