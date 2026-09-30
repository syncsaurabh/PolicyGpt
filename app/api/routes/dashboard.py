from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, require_roles
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    AdminDashboardResponse,
    ApplicationStatusItem,
    CitizenDashboardResponse,
    GovernmentDashboardResponse,
    SavedPolicyCreate,
    SavedPolicyItem,
    SchemeApplicationCreate,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ============================================================================
# 1. CITIZEN DASHBOARD
# ============================================================================

@router.get(
    "/citizen",
    response_model=CitizenDashboardResponse,
    summary="Get Citizen Dashboard",
    description="Retrieve aggregated personalized dashboard for the authenticated citizen including saved policies, eligible schemes, recent notifications, search history, and application statuses.",
    responses={
        200: {"description": "Citizen dashboard data retrieved successfully"},
        401: {"description": "Unauthenticated access"},
        403: {"description": "Forbidden - requires CITIZEN role"},
    },
)
def get_citizen_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CITIZEN)),
) -> CitizenDashboardResponse:
    """Retrieve personalized dashboard strictly isolated to the authenticated citizen."""
    return DashboardService.get_citizen_dashboard(db=db, current_user=current_user)


@router.post(
    "/citizen/saved-policies",
    response_model=SavedPolicyItem,
    status_code=status.HTTP_201_CREATED,
    summary="Bookmark a Policy or Scheme",
    description="Save a policy or scheme to the citizen's personal dashboard bookmarks.",
    responses={
        201: {"description": "Item successfully saved to bookmarks"},
        401: {"description": "Unauthenticated access"},
        403: {"description": "Forbidden - requires CITIZEN role"},
        404: {"description": "Policy or scheme not found"},
    },
)
def save_policy(
    payload: SavedPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CITIZEN)),
) -> SavedPolicyItem:
    """Save or bookmark a policy or scheme for the authenticated citizen."""
    saved = DashboardService.save_policy(
        db=db,
        user_id=current_user.id,
        policy_id=payload.policy_id,
        scheme_id=payload.scheme_id,
        notes=payload.notes,
    )
    if saved.policy:
        return SavedPolicyItem(
            id=saved.id,
            policy_id=saved.policy.id,
            scheme_id=None,
            item_type="policy",
            title=saved.policy.title,
            category=saved.policy.category,
            department=saved.policy.department,
            ministry=saved.policy.ministry,
            state=saved.policy.state,
            sector=saved.policy.sector,
            status=saved.policy.status,
            saved_at=saved.created_at,
            notes=saved.notes,
        )
    elif saved.scheme:
        return SavedPolicyItem(
            id=saved.id,
            policy_id=None,
            scheme_id=saved.scheme.id,
            item_type="scheme",
            title=saved.scheme.name,
            category=saved.scheme.category,
            department=saved.scheme.department,
            ministry=saved.scheme.ministry,
            state=saved.scheme.state,
            sector=saved.scheme.sector,
            status=saved.scheme.status,
            saved_at=saved.created_at,
            notes=saved.notes,
        )
    return SavedPolicyItem(
        id=saved.id,
        policy_id=payload.policy_id,
        scheme_id=payload.scheme_id,
        item_type="policy" if payload.policy_id else "scheme",
        title="Saved Item",
        status="ACTIVE",
        saved_at=saved.created_at,
        notes=saved.notes,
    )


@router.delete(
    "/citizen/saved-policies/{policy_id}",
    summary="Remove a Bookmark",
    description="Remove a saved policy or scheme from the citizen's personal bookmarks.",
    responses={
        200: {"description": "Item removed from bookmarks"},
        401: {"description": "Unauthenticated access"},
        403: {"description": "Forbidden - requires CITIZEN role"},
        404: {"description": "Saved item not found"},
    },
)
def remove_saved_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CITIZEN)),
) -> Dict[str, str]:
    """Remove a bookmarked policy or scheme for the authenticated citizen."""
    DashboardService.remove_saved_policy(db=db, user_id=current_user.id, item_id=policy_id)
    return {"detail": f"Bookmark {policy_id} removed from saved items"}


@router.post(
    "/citizen/applications",
    response_model=ApplicationStatusItem,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Scheme Application",
    description="Submit a scheme application for tracking in citizen dashboard.",
    responses={
        201: {"description": "Scheme application submitted successfully"},
        401: {"description": "Unauthenticated access"},
        403: {"description": "Forbidden - requires CITIZEN role"},
        404: {"description": "Scheme not found"},
    },
)
def submit_scheme_application(
    payload: SchemeApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CITIZEN)),
) -> ApplicationStatusItem:
    """Submit a scheme application for tracking."""
    app_item = DashboardService.submit_application(
        db=db,
        user_id=current_user.id,
        scheme_id=payload.scheme_id,
        details_json=payload.details_json,
        remarks=payload.remarks,
    )
    return ApplicationStatusItem(
        id=app_item.id,
        scheme_id=app_item.scheme_id,
        scheme_name=app_item.scheme.name if app_item.scheme else f"Scheme #{app_item.scheme_id}",
        application_number=app_item.application_number,
        status=app_item.status,
        details_json=app_item.details_json,
        remarks=app_item.remarks,
        created_at=app_item.created_at,
        updated_at=app_item.updated_at,
    )


# ============================================================================
# 2. GOVERNMENT OFFICIAL DASHBOARD
# ============================================================================

@router.get(
    "/government",
    response_model=GovernmentDashboardResponse,
    summary="Get Government Official Dashboard",
    description="Retrieve operational intelligence and department statistics for government officials, including policy statistics, scheme usage, user activity, department reports, and notification statistics.",
    responses={
        200: {"description": "Government dashboard data retrieved successfully"},
        401: {"description": "Unauthenticated access"},
        403: {"description": "Forbidden - requires GOVERNMENT_OFFICIAL or ADMINISTRATOR role"},
    },
)
def get_government_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.GOVERNMENT_OFFICIAL, UserRole.ADMINISTRATOR)),
) -> GovernmentDashboardResponse:
    """Retrieve operational metrics for government officials."""
    return DashboardService.get_government_dashboard(db=db, current_user=current_user)


# ============================================================================
# 3. ADMIN DASHBOARD
# ============================================================================

@router.get(
    "/admin",
    response_model=AdminDashboardResponse,
    summary="Get Administrator Dashboard",
    description="Retrieve comprehensive platform governance data for administrators, including user management, policy pipeline, platform analytics, reports summary, and recent audit logs.",
    responses={
        200: {"description": "Administrator dashboard data retrieved successfully"},
        401: {"description": "Unauthenticated access"},
        403: {"description": "Forbidden - requires ADMINISTRATOR role"},
    },
)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
) -> AdminDashboardResponse:
    """Retrieve governance, compliance, and user metrics for administrators."""
    return DashboardService.get_admin_dashboard(db=db, current_user=current_user)
