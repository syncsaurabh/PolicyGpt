from typing import List
from pydantic import BaseModel
from app.schemas.policy import PolicyRead
from app.schemas.scheme import SchemeRead


class PolicySearchResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    results: List[PolicyRead]


class SchemeSearchResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    results: List[SchemeRead]
