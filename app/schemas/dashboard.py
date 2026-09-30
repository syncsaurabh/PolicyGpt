from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.analytics import (
    DepartmentAnalyticsItem,
    NotificationAnalytics,
    OverviewAnalyticsResponse,
    PolicyAnalytics,
    SchemeAnalytics,
    UsageStatisticsResponse,
    UserAnalytics,
)
from app.schemas.eligibility import SchemeEligibilityResult


# --- Citizen Dashboard Schemas ---

class SavedPolicyItem(BaseModel):
    id: int
    policy_id: Optional[int] = None
    scheme_id: Optional[int] = None
    item_type: str = "policy"  # 'policy' or 'scheme'
    title: str
    category: Optional[str] = None
    department: Optional[str] = None
    ministry: Optional[str] = None
    state: Optional[str] = None
    sector: Optional[str] = None
    status: str
    saved_at: datetime
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SavedPolicyCreate(BaseModel):
    policy_id: Optional[int] = None
    scheme_id: Optional[int] = None
    notes: Optional[str] = None


class CitizenNotificationItem(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    channel: str
    status: str
    is_read: bool
    created_at: datetime
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CitizenSearchHistoryItem(BaseModel):
    id: int
    query: str
    filters_json: Optional[str] = None
    result_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatusItem(BaseModel):
    id: int
    scheme_id: int
    scheme_name: str
    application_number: str
    status: str
    details_json: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SchemeApplicationCreate(BaseModel):
    scheme_id: int
    details_json: Optional[str] = None
    remarks: Optional[str] = None


class CitizenDashboardResponse(BaseModel):
    saved_policies: List[SavedPolicyItem] = Field(default_factory=list, description="Policies and schemes bookmarked by the citizen")
    eligible_schemes: List[SchemeEligibilityResult] = Field(default_factory=list, description="Schemes matching citizen profile eligibility criteria")
    recent_notifications: List[CitizenNotificationItem] = Field(default_factory=list, description="Recent in-app alerts and notifications for the citizen")
    search_history: List[CitizenSearchHistoryItem] = Field(default_factory=list, description="Recent policy and scheme search queries executed by the citizen")
    application_status: List[ApplicationStatusItem] = Field(default_factory=list, description="Tracking statuses of schemes applied by the citizen")

    model_config = ConfigDict(from_attributes=True)


# --- Government Official Dashboard Schemas ---

class GovernmentDashboardResponse(BaseModel):
    policy_statistics: PolicyAnalytics = Field(..., description="Comprehensive policy distribution and status analytics")
    scheme_usage: SchemeAnalytics = Field(..., description="Scheme utilization, category, and status metrics")
    user_activity: UsageStatisticsResponse = Field(..., description="Platform user events and interaction statistics")
    department_reports: List[DepartmentAnalyticsItem] = Field(default_factory=list, description="Department-level policy and scheme statistics")
    notification_statistics: NotificationAnalytics = Field(..., description="Notification volume, delivery channels, and read rates")

    model_config = ConfigDict(from_attributes=True)


# --- Admin Dashboard Schemas ---

class AuditLogItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminReportsSummary(BaseModel):
    total_reports_generated: int = 0
    recent_reports: List[Dict[str, Any]] = Field(default_factory=list)


class AdminDashboardResponse(BaseModel):
    user_management: UserAnalytics = Field(..., description="User registrations, roles, and account status metrics")
    policy_management: PolicyAnalytics = Field(..., description="Policy lifecycle, approval pipeline, and status breakdown")
    analytics: OverviewAnalyticsResponse = Field(..., description="High-level platform overview metrics")
    reports: AdminReportsSummary = Field(..., description="Generated reports summary and recent export logs")
    audit_logs: List[AuditLogItem] = Field(default_factory=list, description="Recent security and governance audit events")

    model_config = ConfigDict(from_attributes=True)
