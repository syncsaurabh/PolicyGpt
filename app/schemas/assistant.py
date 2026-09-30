import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceCitation(BaseModel):
    type: str = Field(..., description="Entity type: 'scheme', 'policy', 'faq', 'eligibility', 'comparison', 'support'")
    id: Optional[Union[int, str]] = Field(None, description="Entity identifier")
    name: str = Field(..., description="Display title or name of the source")
    category: Optional[str] = Field(None, description="Source category or department")
    url: Optional[str] = Field(None, description="Frontend navigation route")
    snippet: Optional[str] = Field(None, description="Relevant excerpt or metadata")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User question or query text")
    conversation_id: Optional[str] = Field(None, description="Existing session UUID or omit to create new")
    profile_context: Optional[Dict[str, Any]] = Field(None, description="Optional profile context (age, state, income, etc.)")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Message cannot be blank")
        return clean


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded response text formulated from PolicyGPT database")
    conversation_id: str = Field(..., description="Unique conversation session UUID")
    intent: str = Field(..., description="Identified query intent (e.g. 'scheme_search', 'eligibility_check')")
    sources: List[SourceCitation] = Field(default_factory=list, description="Direct citations to verified platform entities")
    suggested_questions: List[str] = Field(default_factory=list, description="Follow-up suggestions")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")


class ConversationMessageRead(BaseModel):
    id: int
    role: str
    content: str
    sources: List[SourceCitation] = Field(default_factory=list)
    intent: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    messages: List[ConversationMessageRead]


class ConversationListItem(BaseModel):
    id: str
    title: str
    last_message: Optional[str] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    total_count: int
    results: List[ConversationListItem]
