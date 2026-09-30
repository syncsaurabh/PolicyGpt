from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_optional_current_user
from app.models.user import User
from app.schemas.comparison import ComparisonRequest, ComparisonResponse
from app.services.comparison_service import ComparisonService

router = APIRouter(prefix="/comparison", tags=["Comparison"])


@router.post(
    "",
    response_model=ComparisonResponse,
    summary="Compare 2 to 3 policies or schemes side-by-side",
)
def compare_entities(
    req: ComparisonRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Compare 2 or 3 policies or schemes across parameters:
    - Benefits
    - Eligibility
    - Departments
    - State
    - Application Process

    Validates that:
    - 2 to 3 items are provided
    - No duplicate IDs are submitted
    - All requested items exist and are accessible under the caller's role.
    """
    return ComparisonService.compare(db=db, req=req, current_user=current_user)
