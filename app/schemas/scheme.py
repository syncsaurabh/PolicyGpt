from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.scheme import SchemeStatus, SchemeCategory


# --- Eligibility Rule Schemas ---
class EligibilityRuleBase(BaseModel):
    rule_name: str = Field(..., min_length=2, max_length=255, description="Short identifier for the rule")
    criteria_json: Optional[str] = Field(None, description="JSON string with criteria keys like min_age, max_income, etc.")
    description: Optional[str] = Field(None, description="Human-readable rule explanation")
    is_active: bool = Field(True, description="Rule active status")


class EligibilityRuleCreate(EligibilityRuleBase):
    pass


class EligibilityRuleRead(EligibilityRuleBase):
    id: int
    scheme_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Scheme Schemas ---
class SchemeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Official scheme name")
    description: Optional[str] = Field(None, description="Scheme overview and objectives")
    benefits: Optional[str] = Field(None, description="Financial or material benefits provided")
    target_audience: Optional[str] = Field(None, max_length=255, description="Target beneficiary segment")
    category: Optional[str] = Field(None, max_length=100, description="Scheme category e.g. Scholarships, Farmer Welfare")
    department: Optional[str] = Field(None, max_length=150, description="Administering department")
    ministry: Optional[str] = Field(None, max_length=200, description="Administering ministry")
    state: Optional[str] = Field(None, max_length=100, description="Target state or 'Central'")
    sector: Optional[str] = Field(None, max_length=100, description="Associated sector")
    application_process: Optional[str] = Field(None, description="Step-by-step guidance on how to apply")
    policy_id: Optional[int] = Field(None, description="Linked parent policy ID if any")
    is_active: bool = Field(True, description="Active status for soft archive")


class SchemeCreate(SchemeBase):
    status: Optional[SchemeStatus] = Field(default=SchemeStatus.ACTIVE, description="Scheme operational status")
    eligibility_rules: Optional[List[EligibilityRuleCreate]] = Field(None, description="Initial eligibility rules to attach")


class SchemeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    benefits: Optional[str] = None
    target_audience: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=150)
    ministry: Optional[str] = Field(None, max_length=200)
    state: Optional[str] = Field(None, max_length=100)
    sector: Optional[str] = Field(None, max_length=100)
    application_process: Optional[str] = None
    policy_id: Optional[int] = None
    status: Optional[SchemeStatus] = None
    is_active: Optional[bool] = None


class SchemeRead(SchemeBase):
    id: int
    status: str
    publication_date: Optional[datetime] = None
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SchemeDetailRead(SchemeRead):
    eligibility_rules: List[EligibilityRuleRead] = []


class SchemePaginationResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    results: List[SchemeRead]
