from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.policy import Policy
    from app.models.eligibility import EligibilityRule
    from app.models.user import User


class SchemeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"
    PUBLISHED = "PUBLISHED"
    DRAFT = "DRAFT"


class SchemeCategory(str, Enum):
    SCHOLARSHIPS = "Scholarships"
    FARMER_WELFARE = "Farmer Welfare"
    HEALTHCARE = "Healthcare"
    HOUSING = "Housing"
    BUSINESS_SUPPORT = "Business Support"
    WOMEN_EMPOWERMENT = "Women Empowerment"
    SENIOR_CITIZEN_WELFARE = "Senior Citizen Welfare"
    STUDENT_SCHEMES = "Student Schemes"
    EMPLOYMENT_PROGRAMS = "Employment Programs"
    SOCIAL_SECURITY = "Social Security"


class Scheme(Base):
    """Scheme model supporting full public scheme management and eligibility rules."""
    __tablename__ = "schemes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("policies.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    benefits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_audience: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(150), nullable=True, index=True)
    ministry: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    application_process: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=SchemeStatus.ACTIVE.value, index=True)
    publication_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    policy: Mapped[Optional["Policy"]] = relationship("Policy", back_populates="schemes")
    eligibility_rules: Mapped[List["EligibilityRule"]] = relationship("EligibilityRule", back_populates="scheme", cascade="all, delete-orphan")
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self) -> str:
        return f"<Scheme id={self.id} name='{self.name}' status={self.status}>"
