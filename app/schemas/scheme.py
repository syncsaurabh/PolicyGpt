from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SchemeBase(BaseModel):
    name: str
    description: Optional[str] = None
    benefits: Optional[str] = None
    target_audience: Optional[str] = None
    policy_id: Optional[int] = None
    is_active: bool = True


class SchemeRead(SchemeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

