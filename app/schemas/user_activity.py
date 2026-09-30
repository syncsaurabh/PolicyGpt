from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UserActivityCreate(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=100)
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None


class UserActivityRead(BaseModel):
    id: int
    user_id: Optional[int] = None
    event_type: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserActivityPaginationResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    results: List[UserActivityRead]
