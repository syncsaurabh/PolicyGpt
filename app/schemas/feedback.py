from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.feedback import FeedbackType, FeedbackStatus, FeedbackPriority


class FeedbackCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255, description="Subject or brief summary of the feedback/ticket")
    content: Optional[str] = Field(None, description="Detailed content of the feedback or issue")
    description: Optional[str] = Field(None, description="Alternative alias for content")
    feedback_type: Optional[FeedbackType] = Field(None, description="Type: FEEDBACK, ISSUE, SUPPORT, INQUIRY, SUGGESTION, COMPLAINT")
    type: Optional[FeedbackType] = Field(None, description="Alternative alias for feedback_type")
    category: Optional[str] = Field(None, max_length=100, description="Category classification")
    reference_id: Optional[str] = Field(None, max_length=100, description="Optional application or scheme reference ID")
    application_id: Optional[str] = Field(None, max_length=100, description="Optional application ID alias")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Citizen rating (1-5)")
    priority: FeedbackPriority = Field(default=FeedbackPriority.MEDIUM, description="Priority: LOW, MEDIUM, HIGH, URGENT")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Normalize content vs description
            content_val = data.get("content")
            desc_val = data.get("description")
            if (content_val is None or (isinstance(content_val, str) and not content_val.strip())) and desc_val:
                data["content"] = desc_val
            elif (desc_val is None or (isinstance(desc_val, str) and not desc_val.strip())) and content_val:
                data["description"] = content_val

            if not data.get("content") or (isinstance(data.get("content"), str) and not data.get("content").strip()):
                raise ValueError("Description or content must be provided and cannot be empty")

            # Normalize type vs feedback_type
            type_val = data.get("type")
            fb_type_val = data.get("feedback_type")
            if fb_type_val is None and type_val is not None:
                data["feedback_type"] = type_val
            elif fb_type_val is None and type_val is None:
                data["feedback_type"] = FeedbackType.FEEDBACK

            # Clean subject
            subj = data.get("subject")
            if isinstance(subj, str) and not subj.strip():
                raise ValueError("Subject cannot be empty or blank")

        return data


class FeedbackUpdate(BaseModel):
    status: Optional[FeedbackStatus] = None
    priority: Optional[FeedbackPriority] = None
    category: Optional[str] = None
    admin_response: Optional[str] = None
    resolution: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_resolution(cls, data: Any) -> Any:
        if isinstance(data, dict):
            res = data.get("resolution")
            adm = data.get("admin_response")
            if adm is None and res is not None:
                data["admin_response"] = res
        return data


class FeedbackResolve(BaseModel):
    admin_response: Optional[str] = Field(None, description="Official response or resolution note")
    resolution: Optional[str] = Field(None, description="Official response or resolution note alias")
    status: FeedbackStatus = Field(default=FeedbackStatus.RESOLVED, description="Resolution status (default: RESOLVED)")

    @model_validator(mode="before")
    @classmethod
    def validate_resolution(cls, data: Any) -> Any:
        if isinstance(data, dict):
            res = data.get("resolution")
            adm = data.get("admin_response")
            final_note = adm or res
            if not final_note or (isinstance(final_note, str) and not final_note.strip()):
                raise ValueError("Resolution message ('resolution' or 'admin_response') is required and cannot be empty")
            data["admin_response"] = final_note
            if "status" not in data or data["status"] is None:
                data["status"] = FeedbackStatus.RESOLVED
        return data


class FeedbackRead(BaseModel):
    id: int
    user_id: Optional[int] = None
    feedback_type: str
    type: Optional[str] = None
    category: Optional[str] = None
    subject: str
    content: str
    description: Optional[str] = None
    rating: Optional[int] = None
    status: str
    priority: str
    admin_response: Optional[str] = None
    resolution: Optional[str] = None
    resolved_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    resolver_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def populate_aliases(self) -> "FeedbackRead":
        if self.type is None:
            self.type = self.feedback_type
        if self.description is None:
            self.description = self.content
        if self.resolution is None:
            self.resolution = self.admin_response
        return self


class FeedbackPaginationResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    results: List[FeedbackRead]


class FeedbackHistoryItem(BaseModel):
    id: int
    action: str
    details: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedbackHistoryResponse(BaseModel):
    feedback_id: int
    total_events: int
    history: List[FeedbackHistoryItem]
