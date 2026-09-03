from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PolicyBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    is_active: bool = True


class PolicyRead(PolicyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

