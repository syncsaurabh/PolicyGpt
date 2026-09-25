from typing import List, Optional, Union
from pydantic import BaseModel, Field


class EligibilityCheckRequest(BaseModel):
    age: Optional[int] = Field(None, ge=0, le=130, description="Age in years", examples=[24])
    gender: Optional[str] = Field(None, description="Gender (e.g. 'male', 'female', 'other')", examples=["male"])
    income: Optional[float] = Field(None, ge=0, description="Annual family/individual income in INR", examples=[250000])
    occupation: Optional[str] = Field(None, description="Current occupation (e.g. 'student', 'farmer')", examples=["student"])
    education: Optional[str] = Field(None, description="Highest qualification (e.g. '10th', 'graduate')", examples=["graduate"])
    location: Optional[str] = Field(None, description="State or domicile location", examples=["Maharashtra"])
    social_category: Optional[str] = Field(None, description="Social category (e.g. 'General', 'OBC', 'SC', 'ST')", examples=["General"])
    disability_status: Optional[bool] = Field(False, description="Whether user has registered disability", examples=[False])


class SchemeEligibilityResult(BaseModel):
    scheme_id: int
    scheme_name: str
    eligible: bool
    matched_rules: List[str] = []
    failed_rules: List[str] = []
    category: Optional[str] = None
    benefits: Optional[str] = None
    department: Optional[str] = None
    application_guidance: Optional[str] = None


class EligibilityCheckResponse(BaseModel):
    eligible_schemes: List[SchemeEligibilityResult]
    total_matches: int
