from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, get_db, require_roles
from app.models.report import ReportFormat, ReportType
from app.models.user import User, UserRole
from app.schemas.report import (
    DepartmentReportItem,
    PolicyReportItem,
    ReportDataResponse,
    ReportFilterParams,
    ReportGenerateRequest,
    ReportPaginationResponse,
    ReportRead,
    SchemeReportItem,
    UserActivityReportItem,
)
from app.services.activity_service import ActivityService
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "",
    response_model=ReportPaginationResponse,
    summary="List generated reports history",
)
def list_reports(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
        UserRole.RESEARCHER,
    )),
):
    """Retrieve history of generated report documents."""
    results, total_count, total_pages = ReportService.list_reports(
        db=db, page=page, page_size=page_size, report_type=report_type
    )
    return ReportPaginationResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=[ReportRead.model_validate(r) for r in results],
    )


@router.get(
    "/policies",
    response_model=ReportDataResponse,
    summary="Get policy dataset report in JSON format",
)
def get_policy_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    department: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
        UserRole.RESEARCHER,
    )),
):
    """Retrieve policy dataset with multi-field filtering."""
    filters = ReportFilterParams(
        start_date=start_date,
        end_date=end_date,
        department=department,
        category=category,
        state=state,
        status=status_filter,
    )
    data = ReportService.get_policy_report_data(db=db, filters=filters)
    return ReportDataResponse(
        report_title="Government Policies Comprehensive Report",
        report_type=ReportType.POLICY_REPORT.value,
        generated_at=datetime.now(timezone.utc),
        record_count=len(data),
        filters=filters.model_dump(exclude_unset=True),
        data=data,
    )


@router.get(
    "/schemes",
    response_model=ReportDataResponse,
    summary="Get scheme dataset report in JSON format",
)
def get_scheme_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    department: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
        UserRole.RESEARCHER,
    )),
):
    """Retrieve public schemes dataset with multi-field filtering."""
    filters = ReportFilterParams(
        start_date=start_date,
        end_date=end_date,
        department=department,
        category=category,
        state=state,
        status=status_filter,
    )
    data = ReportService.get_scheme_report_data(db=db, filters=filters)
    return ReportDataResponse(
        report_title="Public Welfare Schemes Comprehensive Report",
        report_type=ReportType.SCHEME_REPORT.value,
        generated_at=datetime.now(timezone.utc),
        record_count=len(data),
        filters=filters.model_dump(exclude_unset=True),
        data=data,
    )


@router.get(
    "/departments",
    response_model=ReportDataResponse,
    summary="Get department metrics report in JSON format",
)
def get_department_report(
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """Retrieve department aggregation report."""
    filters = ReportFilterParams(department=department)
    data = ReportService.get_department_report_data(db=db, filters=filters)
    return ReportDataResponse(
        report_title="Department Performance and Publication Report",
        report_type=ReportType.DEPARTMENT_REPORT.value,
        generated_at=datetime.now(timezone.utc),
        record_count=len(data),
        filters=filters.model_dump(exclude_unset=True),
        data=data,
    )


@router.get(
    "/user-activity",
    response_model=ReportDataResponse,
    summary="Get user activity log report in JSON format",
)
def get_user_activity_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    """Retrieve system user activity logs report (Admin only)."""
    filters = ReportFilterParams(start_date=start_date, end_date=end_date, event_type=event_type)
    data = ReportService.get_user_activity_report_data(db=db, filters=filters)
    return ReportDataResponse(
        report_title="Platform User Activity & Usage Report",
        report_type=ReportType.USER_ACTIVITY_REPORT.value,
        generated_at=datetime.now(timezone.utc),
        record_count=len(data),
        filters=filters.model_dump(exclude_unset=True),
        data=data,
    )


# --- File Export Endpoints (PDF & Excel) ---

@router.get(
    "/export/policies",
    summary="Export policy report as downloadable PDF or Excel file",
)
def export_policy_report(
    format: str = Query("pdf", pattern="^(pdf|excel|xlsx)$", description="Export format: 'pdf' or 'excel'"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    department: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
        UserRole.RESEARCHER,
    )),
):
    """Generate and download server-side PDF or Excel spreadsheet of policies."""
    filters = ReportFilterParams(
        start_date=start_date,
        end_date=end_date,
        department=department,
        category=category,
        state=state,
        status=status_filter,
    )
    raw_data = ReportService.get_policy_report_data(db=db, filters=filters)
    headers = ["ID", "Policy Title", "Category", "Department", "State", "Status", "Created Date"]
    data_rows = [
        [r["id"], r["title"], r["category"], r["department"], r["state"], r["status"], r["created_at"]]
        for r in raw_data
    ]
    filters_dict = filters.model_dump(exclude_unset=True)

    # Log report generation in database and user activities
    ReportService.log_generated_report(
        db=db,
        title="Policy Dataset Report",
        report_type=ReportType.POLICY_REPORT.value,
        file_format=format.upper(),
        record_count=len(raw_data),
        generated_by=current_user.id,
        filters=filters,
    )
    ActivityService.log_activity(
        db=db,
        user_id=current_user.id,
        event_type="REPORT_GENERATED",
        resource_type="PolicyReport",
        details={"format": format, "record_count": len(raw_data)},
    )

    if format.lower() in ("excel", "xlsx"):
        stream = ReportService.export_excel(
            sheet_title="Policies",
            title="Government Policies Report",
            headers=headers,
            data_rows=data_rows,
            filters_summary=filters_dict,
        )
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=policies_report.xlsx"},
        )
    else:
        stream = ReportService.export_pdf(
            title="Government Policies Report",
            headers=headers,
            data_rows=data_rows,
            filters_summary=filters_dict,
        )
        return StreamingResponse(
            stream,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=policies_report.pdf"},
        )


@router.get(
    "/export/schemes",
    summary="Export scheme report as downloadable PDF or Excel file",
)
def export_scheme_report(
    format: str = Query("pdf", pattern="^(pdf|excel|xlsx)$", description="Export format: 'pdf' or 'excel'"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    department: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
        UserRole.RESEARCHER,
    )),
):
    """Generate and download server-side PDF or Excel spreadsheet of public schemes."""
    filters = ReportFilterParams(
        start_date=start_date,
        end_date=end_date,
        department=department,
        category=category,
        state=state,
        status=status_filter,
    )
    raw_data = ReportService.get_scheme_report_data(db=db, filters=filters)
    headers = ["ID", "Scheme Name", "Category", "Department", "Target Audience", "Status", "Created Date"]
    data_rows = [
        [r["id"], r["name"], r["category"], r["department"], r["target_audience"], r["status"], r["created_at"]]
        for r in raw_data
    ]
    filters_dict = filters.model_dump(exclude_unset=True)

    ReportService.log_generated_report(
        db=db,
        title="Public Schemes Report",
        report_type=ReportType.SCHEME_REPORT.value,
        file_format=format.upper(),
        record_count=len(raw_data),
        generated_by=current_user.id,
        filters=filters,
    )

    if format.lower() in ("excel", "xlsx"):
        stream = ReportService.export_excel(
            sheet_title="Schemes",
            title="Public Welfare Schemes Report",
            headers=headers,
            data_rows=data_rows,
            filters_summary=filters_dict,
        )
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=schemes_report.xlsx"},
        )
    else:
        stream = ReportService.export_pdf(
            title="Public Welfare Schemes Report",
            headers=headers,
            data_rows=data_rows,
            filters_summary=filters_dict,
        )
        return StreamingResponse(
            stream,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=schemes_report.pdf"},
        )


@router.get(
    "/export/departments",
    summary="Export department report as downloadable PDF or Excel file",
)
def export_department_report(
    format: str = Query("pdf", pattern="^(pdf|excel|xlsx)$", description="Export format: 'pdf' or 'excel'"),
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """Generate and download server-side PDF or Excel spreadsheet of department analytics."""
    filters = ReportFilterParams(department=department)
    raw_data = ReportService.get_department_report_data(db=db, filters=filters)
    headers = ["Department", "Total Policies", "Published Policies", "Total Schemes", "Active Schemes"]
    data_rows = [
        [r["department"], r["total_policies"], r["published_policies"], r["total_schemes"], r["active_schemes"]]
        for r in raw_data
    ]
    filters_dict = filters.model_dump(exclude_unset=True)

    ReportService.log_generated_report(
        db=db,
        title="Department Performance Report",
        report_type=ReportType.DEPARTMENT_REPORT.value,
        file_format=format.upper(),
        record_count=len(raw_data),
        generated_by=current_user.id,
        filters=filters,
    )

    if format.lower() in ("excel", "xlsx"):
        stream = ReportService.export_excel(
            sheet_title="Departments",
            title="Department Performance & Publication Report",
            headers=headers,
            data_rows=data_rows,
            filters_summary=filters_dict,
        )
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=department_report.xlsx"},
        )
    else:
        stream = ReportService.export_pdf(
            title="Department Performance & Publication Report",
            headers=headers,
            data_rows=data_rows,
            filters_summary=filters_dict,
        )
        return StreamingResponse(
            stream,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=department_report.pdf"},
        )


@router.get(
    "/export/user-activity",
    summary="Export user activity report as downloadable PDF or Excel file",
)
def export_user_activity_report(
    format: str = Query("pdf", pattern="^(pdf|excel|xlsx)$", description="Export format: 'pdf' or 'excel'"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    """Generate and download server-side PDF or Excel spreadsheet of user activity logs."""
    filters = ReportFilterParams(start_date=start_date, end_date=end_date, event_type=event_type)
    raw_data = ReportService.get_user_activity_report_data(db=db, filters=filters)
    headers = ["ID", "User ID", "Event Type", "Resource Type", "Resource ID", "IP Address", "Timestamp"]
    data_rows = [
        [r["id"], r["user_id"], r["event_type"], r["resource_type"], r["resource_id"], r["ip_address"], r["created_at"]]
        for r in raw_data
    ]
    filters_dict = filters.model_dump(exclude_unset=True)

    ReportService.log_generated_report(
        db=db,
        title="User Activity & Usage Report",
        report_type=ReportType.USER_ACTIVITY_REPORT.value,
        file_format=format.upper(),
        record_count=len(raw_data),
        generated_by=current_user.id,
        filters=filters,
    )

    if format.lower() in ("excel", "xlsx"):
        stream = ReportService.export_excel(
            sheet_title="UserActivities",
            title="Platform User Activity Logs Report",
            headers=headers,
            data_rows=data_rows,
            filters_summary=filters_dict,
        )
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=user_activity_report.xlsx"},
        )
    else:
        stream = ReportService.export_pdf(
            title="Platform User Activity Logs Report",
            headers=headers,
            data_rows=data_rows,
            filters_summary=filters_dict,
        )
        return StreamingResponse(
            stream,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=user_activity_report.pdf"},
        )
