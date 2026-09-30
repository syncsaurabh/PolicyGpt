from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's registered email")
    password: str = Field(..., description="User's password")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserRead] = None


class TokenData(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Registered email to receive password reset instructions",
        examples=["user@example.com"]
    )


class MessageResponse(BaseModel):
    message: str = Field(..., description="Response status message", examples=["Operation completed successfully."])


class ForgotPasswordResponse(MessageResponse):
    reset_token: Optional[str] = Field(
        None,
        description="Password reset token (available in development environment for testing convenience)",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6InJlc2V0IiwiZXhwIjoxNzM1NzAwMDAwLCJpYXQiOjE3MzU2OTkxMDAsInN1YiI6InVzZXJAZXhhbXBsZS5jb20ifQ..."]
    )


class ResetPasswordRequest(BaseModel):
    token: str = Field(
        ...,
        description="Password-reset token received from POST /auth/forgot-password (Do NOT use the access token from /login)",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6InJlc2V0IiwiZXhwIjoxNzM1NzAwMDAwLCJpYXQiOjE3MzU2OTkxMDAsInN1YiI6InVzZXJAZXhhbXBsZS5jb20ifQ..."]
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New secure password (minimum 8 characters)",
        examples=["NewSecurePassword123!"]
    )
