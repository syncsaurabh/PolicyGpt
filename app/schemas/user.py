from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models.user import UserRole


class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the user")
    email: EmailStr = Field(..., description="Unique email address")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="Plain text password (min 8 chars)")
    role: Optional[Union[UserRole, str]] = Field(default=UserRole.CITIZEN, description="User role")

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v: Optional[Union[UserRole, str]]) -> UserRole:
        if v is None:
            return UserRole.CITIZEN
        if isinstance(v, UserRole):
            return v
        if isinstance(v, str):
            return UserRole.from_string(v)
        raise ValueError(f"Invalid role: {v}")


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Updated full name")


class UserRead(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
