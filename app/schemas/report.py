from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.report import ReportType, ReportFormat


class ReportFilterParams(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    department: Optional[str] = None
    category: Optional[str] = None
    state: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None
    event_type: Optional[str] = None


class ReportGenerateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF
    filters: Optional[ReportFilterParams] = None


class ReportRead(BaseModel):
    id: int
    generated_by: Optional[int] = None
    title: str
    report_type: str
    file_format: Optional[str] = None
    file_path: Optional[str] = None
    parameters_json: Optional[str] = None
    status: str
    record_count: int
    metadata_json: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportPaginationResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    results: List[ReportRead]


class PolicyReportItem(BaseModel):
    id: int
    title: str
    category: Optional[str] = None
    department: Optional[str] = None
    ministry: Optional[str] = None
    state: Optional[str] = None
    status: str
    publication_date: Optional[datetime] = None
    created_at: datetime


class SchemeReportItem(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    department: Optional[str] = None
    ministry: Optional[str] = None
    state: Optional[str] = None
    status: str
    target_audience: Optional[str] = None
    publication_date: Optional[datetime] = None
    created_at: datetime


class DepartmentReportItem(BaseModel):
    department: str
    policy_count: int
    scheme_count: int
    published_policies: int
    active_schemes: int


class UserActivityReportItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    event_type: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime


class ReportDataResponse(BaseModel):
    report_title: str
    report_type: str
    generated_at: datetime
    record_count: int
    filters: Dict[str, Any]
    data: List[Dict[str, Any]]
