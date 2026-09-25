from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.feedback import FeedbackType, FeedbackStatus, FeedbackPriority


class FeedbackCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    feedback_type: FeedbackType = FeedbackType.FEEDBACK
    category: Optional[str] = Field(None, max_length=100)
    rating: Optional[int] = Field(None, ge=1, le=5)
    priority: FeedbackPriority = FeedbackPriority.MEDIUM


class FeedbackUpdate(BaseModel):
    status: Optional[FeedbackStatus] = None
    priority: Optional[FeedbackPriority] = None
    category: Optional[str] = None
    admin_response: Optional[str] = None


class FeedbackResolve(BaseModel):
    admin_response: str = Field(..., min_length=1, description="Official response or resolution note")
    status: FeedbackStatus = FeedbackStatus.RESOLVED


class FeedbackRead(BaseModel):
    id: int
    user_id: Optional[int] = None
    feedback_type: str
    category: Optional[str] = None
    subject: str
    content: str
    rating: Optional[int] = None
    status: str
    priority: str
    admin_response: Optional[str] = None
    resolved_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FeedbackPaginationResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    results: List[FeedbackRead]
