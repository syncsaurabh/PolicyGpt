from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.application import ApplicationStatus


class ApplicantSummary(BaseModel):
    id: int
    name: str
    email: str
    phone_number: Optional[str] = None
    state: Optional[str] = None
    age: Optional[int] = None
    role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SchemeSummary(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    department: Optional[str] = None
    ministry: Optional[str] = None
    state: Optional[str] = None
    sector: Optional[str] = None
    benefits: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationCreate(BaseModel):
    scheme_id: int = Field(..., description="ID of the welfare scheme being applied for")
    details_json: Optional[str] = Field(None, description="JSON string containing applicant declarations and form responses")
    remarks: Optional[str] = Field(None, description="Optional remarks or notes from applicant")


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus = Field(..., description="New application status")
    remarks: Optional[str] = Field(None, description="Review remarks or decision comments")
    rejection_reason: Optional[str] = Field(None, description="Reason if status is REJECTED")


class ApplicationWithdraw(BaseModel):
    reason: Optional[str] = Field(None, description="Reason for withdrawing application")


class ApplicationRead(BaseModel):
    id: int
    application_number: str
    user_id: int
    scheme_id: int
    scheme_name: str
    status: str
    details_json: Optional[str] = None
    remarks: Optional[str] = None
    reviewed_by_id: Optional[int] = None
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    scheme: Optional[SchemeSummary] = None
    applicant: Optional[ApplicantSummary] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationPaginationResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    results: List[ApplicationRead]
