from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_optional_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.auth import MessageResponse
from app.schemas.faq import FAQCreate, FAQListResponse, FAQRead, FAQUpdate
from app.services.faq_service import FAQService

router = APIRouter(prefix="/faqs", tags=["FAQs & Helpdesk"])


@router.get(
    "",
    response_model=FAQListResponse,
    summary="List Frequently Asked Questions",
)
def list_faqs(
    category: Optional[str] = Query(None, description="Filter by category"),
    keyword: Optional[str] = Query(None, description="Search keyword in question or answer"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Retrieve list of active FAQs for public guidance.
    Admins can view inactive FAQs as well.
    """
    is_admin = current_user is not None and current_user.role == UserRole.ADMINISTRATOR
    faqs = FAQService.list_faqs(
        db=db,
        category=category,
        keyword=keyword,
        is_active_only=not is_admin,
    )
    return FAQListResponse(
        total_count=len(faqs),
        results=[FAQRead.model_validate(f) for f in faqs],
    )


@router.get(
    "/{id}",
    response_model=FAQRead,
    summary="Get single FAQ by ID",
)
def get_faq(
    id: int,
    db: Session = Depends(get_db),
):
    """Retrieve FAQ details by ID."""
    return FAQService.get_faq(db=db, faq_id=id)


@router.post(
    "",
    response_model=FAQRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new FAQ entry",
)
def create_faq(
    faq_in: FAQCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    """Create a new FAQ (Admin only)."""
    return FAQService.create_faq(db=db, faq_in=faq_in, current_user=current_user)


@router.put(
    "/{id}",
    response_model=FAQRead,
    summary="Update FAQ details",
)
def update_faq(
    id: int,
    faq_update: FAQUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    """Update FAQ question, answer, category, or active status (Admin only)."""
    return FAQService.update_faq(db=db, faq_id=id, faq_update=faq_update, current_user=current_user)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    summary="Delete an FAQ entry",
)
def delete_faq(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    """Delete an FAQ (Admin only)."""
    FAQService.delete_faq(db=db, faq_id=id, current_user=current_user)
    return MessageResponse(message="FAQ deleted successfully")
