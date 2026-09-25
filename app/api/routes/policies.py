from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, get_db, get_optional_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.policy import (
    PolicyApprovalAction,
    PolicyCreate,
    PolicyPaginationResponse,
    PolicyRead,
    PolicyUpdate,
)
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/policies")


# --- Policy Management Endpoints ---
@router.post(
    "",
    response_model=PolicyRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Policies"],
    summary="Create a new policy record",
)
def create_policy(
    policy_in: PolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)),
):
    """
    Create a new government policy.
    Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role.
    """
    return PolicyService.create_policy(db=db, policy_in=policy_in, current_user=current_user)


@router.get(
    "",
    response_model=PolicyPaginationResponse,
    tags=["Policies"],
    summary="List policies with pagination, sorting, and filters",
)
def list_policies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. Education, Healthcare)"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. DRAFT, PUBLISHED)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    state: Optional[str] = Query(None, description="Filter by target state"),
    keyword: Optional[str] = Query(None, description="Keyword search in title and description"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction ('asc' or 'desc')"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    List policies.
    Citizens and guests see only active & published policies.
    Officials and Admins can view all statuses.
    """
    results, total_count, total_pages = PolicyService.list_policies(
        db=db,
        page=page,
        page_size=page_size,
        category=category,
        status_filter=status,
        department=department,
        state=state,
        keyword=keyword,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user,
    )
    return PolicyPaginationResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=[PolicyRead.model_validate(p) for p in results],
    )


@router.get(
    "/{id}",
    response_model=PolicyRead,
    tags=["Policies"],
    summary="Retrieve policy details by ID",
)
def get_policy(
    id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Retrieve single policy details by ID.
    Enforces publication check for public/citizen users.
    """
    return PolicyService.get_policy(db=db, policy_id=id, current_user=current_user)


@router.put(
    "/{id}",
    response_model=PolicyRead,
    tags=["Policies"],
    summary="Update policy details",
)
def update_policy(
    id: int,
    policy_in: PolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)),
):
    """
    Update policy information.
    Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role.
    """
    return PolicyService.update_policy(db=db, policy_id=id, policy_in=policy_in, current_user=current_user)


@router.delete(
    "/{id}",
    response_model=PolicyRead,
    tags=["Policies"],
    summary="Soft-delete / archive a policy",
)
def archive_policy(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)),
):
    """
    Archive / soft-delete a policy record.
    Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role.
    """
    return PolicyService.archive_policy(db=db, policy_id=id, current_user=current_user)


# --- Policy Approval Workflow Endpoints ---
@router.post(
    "/{id}/submit",
    response_model=PolicyRead,
    tags=["Policy Approval"],
    summary="Submit a policy for review/approval",
)
def submit_policy_for_approval(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)),
):
    """
    Submit a policy in DRAFT or REJECTED status for administrative approval.
    Transitions status to PENDING_APPROVAL.
    """
    return PolicyService.submit_for_approval(db=db, policy_id=id, current_user=current_user)


@router.post(
    "/{id}/approve",
    response_model=PolicyRead,
    tags=["Policy Approval"],
    summary="Approve a pending policy",
)
def approve_policy(
    id: int,
    action: Optional[PolicyApprovalAction] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)),
):
    """
    Approve a policy in PENDING_APPROVAL status.
    Transitions status to APPROVED (or PUBLISHED if publish=True).
    """
    publish_flag = bool(action.publish) if (action and action.publish is not None) else False
    return PolicyService.approve_policy(db=db, policy_id=id, current_user=current_user, publish=publish_flag)


@router.post(
    "/{id}/reject",
    response_model=PolicyRead,
    tags=["Policy Approval"],
    summary="Reject a pending policy",
)
def reject_policy(
    id: int,
    action: Optional[PolicyApprovalAction] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)),
):
    """
    Reject a policy in PENDING_APPROVAL status.
    Transitions status to REJECTED with feedback reason recorded.
    """
    reason = action.reason if action else None
    return PolicyService.reject_policy(db=db, policy_id=id, current_user=current_user, reason=reason)
