from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DistributionItem(BaseModel):
    name: str
    count: int


class PolicyAnalytics(BaseModel):
    total_policies: int
    published_count: int
    draft_count: int
    pending_approval_count: int
    approved_count: int
    rejected_count: int
    archived_count: int
    by_category: List[DistributionItem]
    by_department: List[DistributionItem]
    by_state: List[DistributionItem]


class SchemeAnalytics(BaseModel):
    total_schemes: int
    active_count: int
    inactive_count: int
    draft_count: int
    archived_count: int
    published_count: int
    by_category: List[DistributionItem]
    by_department: List[DistributionItem]
    by_state: List[DistributionItem]


class UserAnalytics(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    by_role: List[DistributionItem]
    recent_registrations_30d: int


class DepartmentAnalyticsItem(BaseModel):
    department: str
    policy_count: int
    scheme_count: int
    published_policies: int
    active_schemes: int
    activity_count: int


class DepartmentAnalyticsResponse(BaseModel):
    total_departments: int
    departments: List[DepartmentAnalyticsItem]


class SearchAnalytics(BaseModel):
    total_searches: int
    unique_users_count: int
    popular_queries: List[DistributionItem]
    zero_result_searches: int


class NotificationAnalytics(BaseModel):
    total_notifications: int
    unread_count: int
    read_count: int
    by_type: List[DistributionItem]
    by_channel: List[DistributionItem]


class UsageStatisticsResponse(BaseModel):
    total_activities: int
    activities_by_event_type: List[DistributionItem]
    total_searches: int
    total_eligibility_checks: int
    total_feedbacks: int
    total_reports_generated: int
    popular_resources: List[DistributionItem]
    recent_activities: List[Dict[str, Any]]


class OverviewAnalyticsResponse(BaseModel):
    total_policies: int
    published_policies: int
    total_schemes: int
    active_schemes: int
    total_users: int
    total_searches: int
    total_notifications: int
    unread_notifications: int
    policy_category_distribution: List[DistributionItem]
    scheme_category_distribution: List[DistributionItem]
    department_distribution: List[DistributionItem]
    user_role_distribution: List[DistributionItem]
