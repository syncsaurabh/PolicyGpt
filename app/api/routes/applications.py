from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.application import (
    ApplicationCreate,
    ApplicationPaginationResponse,
    ApplicationRead,
    ApplicationStatusUpdate,
    ApplicationWithdraw,
)
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post(
    "",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new Scheme Application",
    description="Citizen creates and submits an application for a welfare scheme.",
    responses={
        201: {"description": "Application submitted successfully with tracking number"},
        401: {"description": "Unauthenticated access"},
        404: {"description": "Scheme not found"},
    },
)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationRead:
    """Submit a scheme application tied strictly to the authenticated user."""
    return ApplicationService.create_application(db=db, current_user=current_user, payload=payload)


@router.get(
    "",
    response_model=ApplicationPaginationResponse,
    summary="List scheme applications with RBAC scoping and filters",
    description="Retrieve paginated applications. Citizens only see their own applications. Officials and Admins see scoped/all applications.",
    responses={
        200: {"description": "Paginated applications retrieved successfully"},
        401: {"description": "Unauthenticated access"},
    },
)
def list_applications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED)"),
    scheme_id: Optional[int] = Query(None, description="Filter by scheme ID"),
    department: Optional[str] = Query(None, description="Filter by administering department"),
    keyword: Optional[str] = Query(None, description="Search keyword in application #, scheme name, or applicant"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationPaginationResponse:
    """List applications with pagination, search, and role isolation."""
    results, total_count, total_pages = ApplicationService.list_applications(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status,
        scheme_id=scheme_id,
        department=department,
        keyword=keyword,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ApplicationPaginationResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=results,
    )


@router.get(
    "/{id}",
    response_model=ApplicationRead,
    summary="Retrieve application details by ID",
    description="Fetch full details for an application. Enforces strict ownership checks for citizens.",
    responses={
        200: {"description": "Application details retrieved successfully"},
        401: {"description": "Unauthenticated access"},
        403: {"description": "Forbidden - Citizen cannot view other applicants' records"},
        404: {"description": "Application not found"},
    },
)
def get_application(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationRead:
    """Retrieve application details with RBAC authorization."""
    return ApplicationService.get_application_by_id(db=db, application_id=id, current_user=current_user)


@router.patch(
    "/{id}/status",
    response_model=ApplicationRead,
    summary="Update application review status",
    description="Authorize Admin or Government Official to transition application status and add remarks.",
    responses={
        200: {"description": "Application status updated and notification dispatched"},
        401: {"description": "Unauthenticated access"},
        403: {"description": "Forbidden - Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role"},
        404: {"description": "Application not found"},
    },
)
def update_application_status_patch(
    id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)),
) -> ApplicationRead:
    """Update status and remarks for an application."""
    return ApplicationService.update_application_status(
        db=db,
        application_id=id,
        payload=payload,
        current_user=current_user,
    )


@router.put(
    "/{id}/status",
    response_model=ApplicationRead,
    summary="Update application review status (PUT alias)",
    description="Alias for PATCH /{id}/status",
    responses={
        200: {"description": "Application status updated"},
        401: {"description": "Unauthenticated access"},
        403: {"description": "Forbidden - Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role"},
        404: {"description": "Application not found"},
    },
)
def update_application_status_put(
    id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)),
) -> ApplicationRead:
    """Update status and remarks for an application."""
    return ApplicationService.update_application_status(
        db=db,
        application_id=id,
        payload=payload,
        current_user=current_user,
    )


@router.post(
    "/{id}/withdraw",
    response_model=ApplicationRead,
    summary="Withdraw submitted application",
    description="Allows applicant to withdraw an in-progress application.",
    responses={
        200: {"description": "Application successfully withdrawn"},
        400: {"description": "Cannot withdraw approved or disbursed application"},
        401: {"description": "Unauthenticated access"},
        403: {"description": "Forbidden"},
        404: {"description": "Application not found"},
    },
)
def withdraw_application(
    id: int,
    payload: ApplicationWithdraw = ApplicationWithdraw(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationRead:
    """Withdraw an application submitted by the citizen."""
    return ApplicationService.withdraw_application(
        db=db,
        application_id=id,
        current_user=current_user,
        reason=payload.reason,
    )
