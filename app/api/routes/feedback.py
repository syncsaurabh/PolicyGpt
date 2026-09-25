from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, get_db, get_optional_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.feedback import (
    FeedbackCreate,
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
    Submit a citizen feedback, portal issue, or support ticket.
    Supports authenticated users and guest submissions.
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
        category=feedback.category,
        subject=feedback.subject,
        content=feedback.content,
        rating=feedback.rating,
        status=feedback.status,
        priority=feedback.priority,
        admin_response=feedback.admin_response,
        resolved_by_id=feedback.resolved_by_id,
        resolved_at=feedback.resolved_at,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
        user_name=current_user.name if current_user else None,
        user_email=current_user.email if current_user else None,
    )


@router.get(
    "/my",
    response_model=FeedbackPaginationResponse,
    summary="List feedback and support tickets submitted by current user",
)
def list_my_feedback(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status (SUBMITTED, RESOLVED, etc.)"),
    feedback_type: Optional[str] = Query(None, description="Filter by type (FEEDBACK, ISSUE, etc.)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve history and resolution status of the authenticated user's submitted tickets."""
    results, total_count, total_pages = FeedbackService.list_feedback(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        feedback_type=feedback_type,
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
    summary="List and filter all feedback and support tickets",
)
def list_feedback(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status (SUBMITTED, IN_REVIEW, RESOLVED, CLOSED)"),
    feedback_type: Optional[str] = Query(None, description="Filter by type (FEEDBACK, ISSUE, INQUIRY, SUGGESTION, COMPLAINT)"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, MEDIUM, HIGH, URGENT)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """
    List all platform feedback and support tickets with multi-field filtering.
    Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role.
    """
    results, total_count, total_pages = FeedbackService.list_feedback(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        feedback_type=feedback_type,
        priority=priority,
        category=category,
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
    summary="Get feedback ticket details",
)
def get_feedback(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve feedback details by ID.
    Citizens can only view their own tickets; Administrators and Officials can view any ticket.
    """
    f = FeedbackService.get_feedback(db=db, feedback_id=id, current_user=current_user)
    return FeedbackRead(
        id=f.id,
        user_id=f.user_id,
        feedback_type=f.feedback_type,
        category=f.category,
        subject=f.subject,
        content=f.content,
        rating=f.rating,
        status=f.status,
        priority=f.priority,
        admin_response=f.admin_response,
        resolved_by_id=f.resolved_by_id,
        resolved_at=f.resolved_at,
        created_at=f.created_at,
        updated_at=f.updated_at,
        user_name=f.user.name if f.user else None,
        user_email=f.user.email if f.user else None,
    )


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
        category=f.category,
        subject=f.subject,
        content=f.content,
        rating=f.rating,
        status=f.status,
        priority=f.priority,
        admin_response=f.admin_response,
        resolved_by_id=f.resolved_by_id,
        resolved_at=f.resolved_at,
        created_at=f.created_at,
        updated_at=f.updated_at,
        user_name=f.user.name if f.user else None,
        user_email=f.user.email if f.user else None,
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
        category=f.category,
        subject=f.subject,
        content=f.content,
        rating=f.rating,
        status=f.status,
        priority=f.priority,
        admin_response=f.admin_response,
        resolved_by_id=f.resolved_by_id,
        resolved_at=f.resolved_at,
        created_at=f.created_at,
        updated_at=f.updated_at,
        user_name=f.user.name if f.user else None,
        user_email=f.user.email if f.user else None,
    )
