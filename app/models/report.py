from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ReportType(str, Enum):
    POLICY_REPORT = "POLICY_REPORT"
    SCHEME_REPORT = "SCHEME_REPORT"
    DEPARTMENT_REPORT = "DEPARTMENT_REPORT"
    USER_ACTIVITY_REPORT = "USER_ACTIVITY_REPORT"
    ANALYTICS_REPORT = "ANALYTICS_REPORT"


class ReportFormat(str, Enum):
    PDF = "PDF"
    EXCEL = "EXCEL"
    JSON = "JSON"


class Report(Base):
    """Reports generated and exported across policy, scheme, department, and analytics datasets."""
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    generated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    file_format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    parameters_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    generator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[generated_by])

    def __repr__(self) -> str:
        return f"<Report id={self.id} title='{self.title}' type={self.report_type} status={self.status}>"
