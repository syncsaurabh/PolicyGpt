from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_optional_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.auth import MessageResponse
from app.schemas.faq import FAQCreate, FAQListResponse, FAQRead, FAQUpdate
from app.services.faq_service import FAQService

router = APIRouter(prefix="/faqs", tags=["FAQs & Help Desk"])


@router.get(
    "",
    response_model=FAQListResponse,
    summary="List Frequently Asked Questions (Public & Citizen Help Desk)",
)
def list_faqs(
    category: Optional[str] = Query(None, description="Filter by category"),
    keyword: Optional[str] = Query(None, description="Search keyword in question or answer"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Retrieve list of active FAQs for public guidance and help desk queries.
    Public citizens can view active published FAQs.
    Administrators and Officials can view all active and inactive FAQs.
    """
    is_privileged = current_user is not None and current_user.role in (
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )
    faqs, total_count, total_pages = FAQService.list_faqs(
        db=db,
        category=category,
        keyword=keyword,
        is_active_only=not is_privileged,
        page=page,
        page_size=page_size,
    )
    return FAQListResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
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
    """Retrieve FAQ details by ID. Accessible to public citizens and guests."""
    return FAQService.get_faq(db=db, faq_id=id)


@router.post(
    "",
    response_model=FAQRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new FAQ entry (Admin only)",
)
def create_faq(
    faq_in: FAQCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """Create a new FAQ entry. Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role."""
    return FAQService.create_faq(db=db, faq_in=faq_in, current_user=current_user)


@router.put(
    "/{id}",
    response_model=FAQRead,
    summary="Update FAQ details (Admin only)",
)
def update_faq(
    id: int,
    faq_update: FAQUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """Update FAQ question, answer, category, or active status. Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role."""
    return FAQService.update_faq(db=db, faq_id=id, faq_update=faq_update, current_user=current_user)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    summary="Delete an FAQ entry (Admin only)",
)
def delete_faq(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """Delete an FAQ entry. Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role."""
    FAQService.delete_faq(db=db, faq_id=id, current_user=current_user)
    return MessageResponse(message="FAQ deleted successfully")
