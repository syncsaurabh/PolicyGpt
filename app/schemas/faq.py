from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FAQCreate(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="FAQ question text")
    answer: str = Field(..., min_length=1, description="FAQ answer content")
    category: Optional[str] = Field(None, max_length=100, description="FAQ category")
    is_active: bool = Field(default=True, description="Whether FAQ is visible to the public")
    display_order: int = Field(default=0, description="Ordering index for display")


class FAQUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    answer: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class FAQRead(BaseModel):
    id: int
    question: str
    answer: str
    category: Optional[str] = None
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FAQListResponse(BaseModel):
    total_count: int
    page: Optional[int] = 1
    page_size: Optional[int] = 50
    total_pages: Optional[int] = 1
    results: List[FAQRead]
