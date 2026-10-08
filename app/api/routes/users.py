from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get Current User Profile",
)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve current authenticated user profile.
    """
    return current_user


@router.put(
    "/me",
    response_model=UserRead,
    summary="Update Current User Profile",
)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update safe profile information for the current authenticated user.
    
    Editable fields:
    - **name**: User's full name (2–100 characters)
    - **phone_number**: Contact phone number for communications and SMS notifications (max 50 characters)
    - **age**: Age of the user in years (1–120)
    - **state**: State or Union Territory of residence (max 100 characters)
    - **address**: Residential or postal address (max 500 characters)
    - **pincode**: Postal PIN / ZIP code (max 20 characters)
    
    Protected fields (id, email, password_hash, role, is_active, created_at, updated_at) cannot be modified through this endpoint.
    """
    update_data = user_update.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] is not None:
        current_user.name = update_data["name"].strip()

    if "phone_number" in update_data:
        current_user.phone_number = update_data["phone_number"].strip() if update_data["phone_number"] is not None else None

    if "age" in update_data:
        current_user.age = update_data["age"]

    if "state" in update_data:
        current_user.state = update_data["state"].strip() if update_data["state"] is not None else None

    if "address" in update_data:
        current_user.address = update_data["address"].strip() if update_data["address"] is not None else None

    if "pincode" in update_data:
        current_user.pincode = update_data["pincode"].strip() if update_data["pincode"] is not None else None

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
