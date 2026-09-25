from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.policy import PolicyStatus, PolicyCategory


class PolicyBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Official policy title")
    description: Optional[str] = Field(None, description="Detailed policy description and scope")
    category: Optional[str] = Field(None, max_length=100, description="Policy category e.g. Education, Healthcare")
    department: Optional[str] = Field(None, max_length=150, description="Nodal department")
    ministry: Optional[str] = Field(None, max_length=200, description="Parent ministry")
    state: Optional[str] = Field(None, max_length=100, description="Target state or 'Central'")
    sector: Optional[str] = Field(None, max_length=100, description="Economic or social sector")
    is_active: bool = Field(True, description="Active status for soft archive")


class PolicyCreate(PolicyBase):
    status: Optional[PolicyStatus] = Field(default=PolicyStatus.DRAFT, description="Initial lifecycle status")


class PolicyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=150)
    ministry: Optional[str] = Field(None, max_length=200)
    state: Optional[str] = Field(None, max_length=100)
    sector: Optional[str] = Field(None, max_length=100)
    status: Optional[PolicyStatus] = None
    is_active: Optional[bool] = None


class PolicyApprovalAction(BaseModel):
    reason: Optional[str] = Field(None, description="Rejection reason or review feedback")
    publish: Optional[bool] = Field(False, description="If true on approval, set status directly to PUBLISHED")


class PolicyRead(PolicyBase):
    id: int
    status: str
    publication_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_by_id: Optional[int] = None
    approved_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PolicyPaginationResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    results: List[PolicyRead]
