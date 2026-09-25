from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.analytics import (
    DepartmentAnalyticsResponse,
    NotificationAnalytics,
    OverviewAnalyticsResponse,
    PolicyAnalytics,
    SchemeAnalytics,
    SearchAnalytics,
    UsageStatisticsResponse,
    UserAnalytics,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/overview",
    response_model=OverviewAnalyticsResponse,
    summary="Get platform overview analytics and KPIs",
)
def get_overview_analytics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
        UserRole.RESEARCHER,
        UserRole.ORGANIZATION,
    )),
):
    """Retrieve platform overview analytics, category distributions, and totals."""
    return AnalyticsService.get_overview_analytics(db=db, start_date=start_date, end_date=end_date)


@router.get(
    "/policies",
    response_model=PolicyAnalytics,
    summary="Get policy statistics, status breakdown, and distributions",
)
def get_policy_analytics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
        UserRole.RESEARCHER,
    )),
):
    """Retrieve detailed policy metrics, status counts, and department distributions."""
    return AnalyticsService.get_policy_analytics(
        db=db, start_date=start_date, end_date=end_date, department=department
    )


@router.get(
    "/schemes",
    response_model=SchemeAnalytics,
    summary="Get scheme statistics, operational status, and distributions",
)
def get_scheme_analytics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
        UserRole.RESEARCHER,
    )),
):
    """Retrieve scheme metrics, category distributions, and status breakdown."""
    return AnalyticsService.get_scheme_analytics(
        db=db, start_date=start_date, end_date=end_date, department=department
    )


@router.get(
    "/users",
    response_model=UserAnalytics,
    summary="Get user management demographics and growth statistics",
)
def get_user_analytics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    """Retrieve user counts by role, active/inactive proportions, and recent growth (Admin only)."""
    return AnalyticsService.get_user_analytics(db=db, start_date=start_date, end_date=end_date)


@router.get(
    "/departments",
    response_model=DepartmentAnalyticsResponse,
    summary="Get department-level analytics and publication statistics",
)
def get_department_analytics(
    department: Optional[str] = Query(None, description="Filter by department name"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """Retrieve department-level policy, scheme, and operational metrics."""
    return AnalyticsService.get_department_analytics(
        db=db, department_filter=department, start_date=start_date, end_date=end_date
    )


@router.get(
    "/search",
    response_model=SearchAnalytics,
    summary="Get search activity and popular queries analytics",
)
def get_search_analytics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """Retrieve popular search queries, total volume, and zero-result rates."""
    return AnalyticsService.get_search_analytics(db=db, start_date=start_date, end_date=end_date)


@router.get(
    "/notifications",
    response_model=NotificationAnalytics,
    summary="Get notification delivery and engagement analytics",
)
def get_notification_analytics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """Retrieve notification volume, delivery channels, and read/unread statistics."""
    return AnalyticsService.get_notification_analytics(db=db, start_date=start_date, end_date=end_date)


@router.get(
    "/usage",
    response_model=UsageStatisticsResponse,
    summary="Get platform usage statistics and event counts",
)
def get_usage_statistics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """Retrieve platform usage activity logs, eligibility checks, and report counts."""
    return AnalyticsService.get_usage_statistics(db=db, start_date=start_date, end_date=end_date)
