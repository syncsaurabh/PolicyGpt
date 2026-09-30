from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, get_db, get_optional_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackHistoryResponse,
    FeedbackPaginationResponse,
    FeedbackRead,
    FeedbackResolve,
    FeedbackUpdate,
)
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Feedback & Support"])


@router.post(
    "",
    response_model=FeedbackRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit citizen feedback, issue report, or support request",
)
def submit_feedback(
    feedback_in: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Submit citizen feedback, portal issue report, or help desk support ticket.
    
    Supported types:
    - **FEEDBACK**: General citizen feedback and portal suggestions
    - **ISSUE**: Technical problem or bug reporting
    - **SUPPORT**: Help desk or inquiry ticket
    
    If authenticated via Bearer token, the authenticated citizen is automatically assigned as ticket owner.
    Clients cannot override ownership by providing user_id in the body.
    """
    client_ip = request.client.host if request.client else None
    feedback = FeedbackService.create_feedback(
        db=db,
        feedback_in=feedback_in,
        current_user=current_user,
        ip_address=client_ip,
    )
    return FeedbackRead(
        id=feedback.id,
        user_id=feedback.user_id,
        feedback_type=feedback.feedback_type,
        type=feedback.feedback_type,
        category=feedback.category,
        subject=feedback.subject,
        content=feedback.content,
        description=feedback.content,
        rating=feedback.rating,
        status=feedback.status,
        priority=feedback.priority,
        admin_response=feedback.admin_response,
        resolution=feedback.admin_response,
        resolved_by_id=feedback.resolved_by_id,
        resolved_at=feedback.resolved_at,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
        user_name=current_user.name if current_user else None,
        user_email=current_user.email if current_user else None,
        resolver_name=feedback.resolver.name if feedback.resolver else None,
    )


@router.get(
    "/my",
    response_model=FeedbackPaginationResponse,
    summary="List feedback and support tickets submitted by current user",
)
def list_my_feedback(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, SUBMITTED, IN_REVIEW, RESOLVED, CLOSED)"),
    status_filter: Optional[str] = Query(None, description="Legacy alias for status"),
    feedback_type: Optional[str] = Query(None, description="Filter by type (FEEDBACK, ISSUE, SUPPORT, etc.)"),
    type: Optional[str] = Query(None, description="Alias for feedback_type"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, MEDIUM, HIGH, URGENT)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve history and resolution status of the authenticated citizen's submitted tickets.
    Isolated strictly to the authenticated user's own tickets.
    """
    effective_status = status or status_filter
    effective_type = feedback_type or type
    results, total_count, total_pages = FeedbackService.list_feedback(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=effective_status,
        feedback_type=effective_type,
        priority=priority,
        category=category,
        my_only=True,
    )
    return FeedbackPaginationResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=results,
    )


@router.get(
    "",
    response_model=FeedbackPaginationResponse,
    summary="List and filter all feedback and support tickets (Admin / Support)",
)
def list_feedback(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, SUBMITTED, IN_PROGRESS, IN_REVIEW, RESOLVED, CLOSED)"),
    status_filter: Optional[str] = Query(None, description="Legacy alias for status"),
    feedback_type: Optional[str] = Query(None, description="Filter by type (FEEDBACK, ISSUE, SUPPORT, INQUIRY, SUGGESTION, COMPLAINT)"),
    type: Optional[str] = Query(None, description="Alias for feedback_type"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, MEDIUM, HIGH, URGENT)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    user_id: Optional[int] = Query(None, description="Filter by submitting user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter tickets created on or after date"),
    end_date: Optional[datetime] = Query(None, description="Filter tickets created on or before date"),
    sort_by: Optional[str] = Query("created_at", description="Sort field (created_at, priority, status)"),
    sort_order: Optional[str] = Query("desc", description="Sort direction (asc, desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """
    List all platform feedback, support tickets, and issues with multi-field filtering.
    Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role.
    """
    effective_status = status or status_filter
    effective_type = feedback_type or type
    results, total_count, total_pages = FeedbackService.list_feedback(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=effective_status,
        feedback_type=effective_type,
        priority=priority,
        category=category,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
        my_only=False,
    )
    return FeedbackPaginationResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=results,
    )


@router.get(
    "/{id}",
    response_model=FeedbackRead,
    summary="Get feedback or support ticket details",
)
def get_feedback(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve feedback details by ID.
    Citizens can only view their own tickets; Administrators and Officials can view any ticket.
    Returns 403 Forbidden if accessed by unauthorized citizen.
    """
    f = FeedbackService.get_feedback(db=db, feedback_id=id, current_user=current_user)
    return FeedbackRead(
        id=f.id,
        user_id=f.user_id,
        feedback_type=f.feedback_type,
        type=f.feedback_type,
        category=f.category,
        subject=f.subject,
        content=f.content,
        description=f.content,
        rating=f.rating,
        status=f.status,
        priority=f.priority,
        admin_response=f.admin_response,
        resolution=f.admin_response,
        resolved_by_id=f.resolved_by_id,
        resolved_at=f.resolved_at,
        created_at=f.created_at,
        updated_at=f.updated_at,
        user_name=f.user.name if f.user else None,
        user_email=f.user.email if f.user else None,
        resolver_name=f.resolver.name if f.resolver else None,
    )


@router.get(
    "/{id}/history",
    response_model=FeedbackHistoryResponse,
    summary="Get ticket lifecycle and resolution history",
)
def get_feedback_history(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve chronological lifecycle and audit events for a feedback or support ticket.
    Citizens can view history of their own tickets; Administrators can view history of any ticket.
    """
    return FeedbackService.get_feedback_history(db=db, feedback_id=id, current_user=current_user)


@router.put(
    "/{id}/status",
    response_model=FeedbackRead,
    summary="Update feedback status or priority",
)
def update_feedback_status(
    id: int,
    feedback_update: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """
    Update the triage status, priority, or category of a feedback ticket.
    Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role.
    """
    f = FeedbackService.update_feedback(
        db=db, feedback_id=id, feedback_update=feedback_update, current_user=current_user
    )
    return FeedbackRead(
        id=f.id,
        user_id=f.user_id,
        feedback_type=f.feedback_type,
        type=f.feedback_type,
        category=f.category,
        subject=f.subject,
        content=f.content,
        description=f.content,
        rating=f.rating,
        status=f.status,
        priority=f.priority,
        admin_response=f.admin_response,
        resolution=f.admin_response,
        resolved_by_id=f.resolved_by_id,
        resolved_at=f.resolved_at,
        created_at=f.created_at,
        updated_at=f.updated_at,
        user_name=f.user.name if f.user else None,
        user_email=f.user.email if f.user else None,
        resolver_name=f.resolver.name if f.resolver else None,
    )


@router.post(
    "/{id}/resolve",
    response_model=FeedbackRead,
    summary="Post query resolution response to feedback or support ticket",
)
def resolve_feedback(
    id: int,
    resolve_in: FeedbackResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """
    Post official resolution remarks for a ticket and notify the submitting citizen.
    Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role.
    """
    f = FeedbackService.resolve_feedback(
        db=db, feedback_id=id, resolve_in=resolve_in, current_user=current_user
    )
    return FeedbackRead(
        id=f.id,
        user_id=f.user_id,
        feedback_type=f.feedback_type,
        type=f.feedback_type,
        category=f.category,
        subject=f.subject,
        content=f.content,
        description=f.content,
        rating=f.rating,
        status=f.status,
        priority=f.priority,
        admin_response=f.admin_response,
        resolution=f.admin_response,
        resolved_by_id=f.resolved_by_id,
        resolved_at=f.resolved_at,
        created_at=f.created_at,
        updated_at=f.updated_at,
        user_name=f.user.name if f.user else None,
        user_email=f.user.email if f.user else None,
        resolver_name=f.resolver.name if f.resolver else None,
    )
