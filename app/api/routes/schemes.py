from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_optional_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.scheme import (
    EligibilityRuleCreate,
    EligibilityRuleRead,
    SchemeCreate,
    SchemeDetailRead,
    SchemePaginationResponse,
    SchemeRead,
    SchemeUpdate,
)
from app.services.scheme_service import SchemeService

router = APIRouter(prefix="/schemes", tags=["Schemes"])


@router.post(
    "",
    response_model=SchemeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new public scheme",
)
def create_scheme(
    scheme_in: SchemeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)),
):
    """
    Register a new government scheme with optional initial eligibility rules.
    Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role.
    """
    return SchemeService.create_scheme(db=db, scheme_in=scheme_in, current_user=current_user)


@router.get(
    "",
    response_model=SchemePaginationResponse,
    summary="List public schemes with filters and pagination",
)
def list_schemes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by scheme category"),
    status: Optional[str] = Query(None, description="Filter by operational status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    state: Optional[str] = Query(None, description="Filter by state"),
    policy_id: Optional[int] = Query(None, description="Filter by parent policy ID"),
    keyword: Optional[str] = Query(None, description="Keyword search in name and description"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction ('asc' or 'desc')"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    List schemes.
    Citizens and guests see only active schemes.
    Officials and Admins can view all statuses.
    """
    results, total_count, total_pages = SchemeService.list_schemes(
        db=db,
        page=page,
        page_size=page_size,
        category=category,
        status_filter=status,
        department=department,
        state=state,
        policy_id=policy_id,
        keyword=keyword,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user,
    )
    return SchemePaginationResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=[SchemeRead.model_validate(s) for s in results],
    )


@router.get(
    "/{id}",
    response_model=SchemeDetailRead,
    summary="Retrieve scheme details and eligibility rules",
)
def get_scheme(
    id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Retrieve full details of a specific scheme, including all associated eligibility rules.
    """
    return SchemeService.get_scheme(db=db, scheme_id=id, current_user=current_user)


@router.put(
    "/{id}",
    response_model=SchemeRead,
    summary="Update scheme details",
)
def update_scheme(
    id: int,
    scheme_in: SchemeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)),
):
    """
    Update scheme fields.
    Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role.
    """
    return SchemeService.update_scheme(db=db, scheme_id=id, scheme_in=scheme_in, current_user=current_user)


@router.delete(
    "/{id}",
    response_model=SchemeRead,
    summary="Soft-delete / archive a scheme",
)
def archive_scheme(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)),
):
    """
    Soft-delete / archive a scheme.
    Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role.
    """
    return SchemeService.archive_scheme(db=db, scheme_id=id, current_user=current_user)


@router.post(
    "/{id}/rules",
    response_model=EligibilityRuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add an eligibility rule to a scheme",
)
def add_scheme_rule(
    id: int,
    rule_in: EligibilityRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)),
):
    """
    Add a new eligibility rule to an existing scheme.
    Requires ADMINISTRATOR or GOVERNMENT_OFFICIAL role.
    """
    return SchemeService.add_eligibility_rule(db=db, scheme_id=id, rule_in=rule_in, current_user=current_user)
