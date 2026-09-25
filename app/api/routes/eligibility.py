from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.schemas.eligibility import EligibilityCheckRequest, EligibilityCheckResponse
from app.services.eligibility_service import EligibilityService

router = APIRouter(prefix="/eligibility", tags=["Eligibility"])


@router.post(
    "/check",
    response_model=EligibilityCheckResponse,
    summary="Evaluate citizen profile against public schemes using database eligibility rules",
)
def check_eligibility(
    profile: EligibilityCheckRequest,
    db: Session = Depends(get_db),
):
    """
    Check eligibility for government schemes based on user profile parameters:
    - age
    - gender
    - income
    - occupation
    - education
    - location
    - social category
    - disability status

    Evaluates live schemes against actual eligibility rules stored in the database.
    Returns matched rules, reasons for eligibility/ineligibility, and application guidance.
    """
    return EligibilityService.check_eligibility(db=db, profile=profile)
