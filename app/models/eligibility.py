from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.scheme import Scheme


class EligibilityRule(Base):
    """Foundation model for Eligibility Rules."""
    __tablename__ = "eligibility_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scheme_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    criteria_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    scheme: Mapped[Optional["Scheme"]] = relationship("Scheme", back_populates="eligibility_rules")

    def __repr__(self) -> str:
        return f"<EligibilityRule id={self.id} rule_name='{self.rule_name}' scheme_id={self.scheme_id}>"
