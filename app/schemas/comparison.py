from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field, model_validator


class ComparisonRequest(BaseModel):
    scheme_ids: Optional[List[Union[int, str]]] = Field(None, description="2 to 3 scheme IDs to compare", examples=[[1, 2]])
    policy_ids: Optional[List[Union[int, str]]] = Field(None, description="2 to 3 policy IDs to compare", examples=[[1, 2]])

    @model_validator(mode="after")
    def validate_comparison_ids(self) -> "ComparisonRequest":
        if not self.scheme_ids and not self.policy_ids:
            raise ValueError("Either 'scheme_ids' or 'policy_ids' must be provided.")
        if self.scheme_ids and self.policy_ids:
            raise ValueError("Compare either schemes or policies in a single request, not both.")

        ids = self.scheme_ids if self.scheme_ids is not None else self.policy_ids
        if ids is None:
            raise ValueError("Either 'scheme_ids' or 'policy_ids' must be provided.")
        if len(ids) < 2:
            raise ValueError("Comparison requires at least 2 items.")
        if len(ids) > 3:
            raise ValueError("Comparison supports a maximum of 3 items.")

        # Check duplicates
        id_str_list = [str(i) for i in ids]
        if len(set(id_str_list)) != len(id_str_list):
            raise ValueError("Duplicate IDs are not allowed in comparison.")

        return self


class ComparisonItem(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    benefits: Any = []
    eligibility: Any = []
    department: Optional[str] = None
    state: Optional[str] = None
    application_process: Optional[str] = None


class ComparisonResponse(BaseModel):
    comparison_type: str = Field(..., description="'scheme' or 'policy'")
    items: List[ComparisonItem]
