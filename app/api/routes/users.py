from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve current authenticated user profile.
    """
    return current_user


@router.put("/me", response_model=UserRead)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update safe profile information for the current authenticated user.
    Protected fields (id, email, password_hash, role, is_active) cannot be modified here.
    """
    if user_update.name is not None:
        current_user.name = user_update.name.strip()

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


# RBAC Verification Endpoints
@router.get(
    "/admin/test",
    dependencies=[Depends(require_roles(UserRole.ADMINISTRATOR))],
    summary="RBAC verification endpoint for Administrator role"
)
def admin_only_test(current_user: User = Depends(get_current_user)):
    """Only users with ADMINISTRATOR role can access this endpoint."""
    return {
        "status": "ok",
        "message": "Welcome Administrator! Admin access granted. RBAC check passed.",
        "user_id": current_user.id,
        "role": current_user.role.value
    }



@router.get(
    "/government/test",
    dependencies=[Depends(require_roles(UserRole.GOVERNMENT_OFFICIAL))],
    summary="RBAC verification endpoint for Government Official role"
)
def government_only_test(current_user: User = Depends(get_current_user)):
    """Only users with GOVERNMENT_OFFICIAL role can access this endpoint."""
    return {
        "status": "ok",
        "message": "Welcome Government Official! RBAC check passed.",
        "user_id": current_user.id,
        "role": current_user.role.value
    }
