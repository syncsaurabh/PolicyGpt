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
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated full name of the user",
        examples=["Jane Doe"],
    )
    phone_number: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Updated contact phone number for SMS notifications and communication",
        examples=["+919876543210"],
    )
    age: Optional[int] = Field(
        default=None,
        ge=1,
        le=120,
        description="Age of the user in years",
        examples=[28],
    )
    state: Optional[str] = Field(
        default=None,
        max_length=100,
        description="State or Union Territory of residence",
        examples=["Maharashtra"],
    )
    address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Residential / postal address",
        examples=["123 MG Road, Shivajinagar"],
    )
    pincode: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Postal PIN / ZIP code",
        examples=["411005"],
    )


class UserRead(UserBase):
    id: int
    phone_number: Optional[str] = Field(default=None, description="Contact phone number")
    age: Optional[int] = Field(default=None, description="Age in years")
    state: Optional[str] = Field(default=None, description="State of residence")
    address: Optional[str] = Field(default=None, description="Postal address")
    pincode: Optional[str] = Field(default=None, description="Postal PIN code")
    role: UserRole
    is_active: bool
    is_verified: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
