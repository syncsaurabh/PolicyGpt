from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.policy import Policy
    from app.models.scheme import Scheme
    from app.models.user import User


class SavedPolicy(Base):
    """Saved/bookmarked policy or scheme by a citizen user."""
    __tablename__ = "saved_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), nullable=True, index=True)
    scheme_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=True, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    policy: Mapped[Optional["Policy"]] = relationship("Policy", foreign_keys=[policy_id])
    scheme: Mapped[Optional["Scheme"]] = relationship("Scheme", foreign_keys=[scheme_id])

    def __repr__(self) -> str:
        return f"<SavedPolicy id={self.id} user_id={self.user_id} policy_id={self.policy_id} scheme_id={self.scheme_id}>"
