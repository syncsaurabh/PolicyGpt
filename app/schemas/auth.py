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


class VerifyOTPRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="User's registered email address",
        examples=["user@example.com"]
    )
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit OTP verification code",
        examples=["123456"]
    )


class ResendOTPRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="User's registered email address to resend OTP",
        examples=["user@example.com"]
    )


class RegisterResponse(BaseModel):
    message: str = Field(
        ...,
        description="Response status message",
        examples=["Registration successful. Please verify your email with the 6-digit code sent to your inbox."]
    )
    email: str = Field(..., description="Registered email address")
    requires_verification: bool = Field(default=True, description="Whether email verification is required")
    otp: Optional[str] = Field(default=None, description="Generated 6-digit OTP verification code")
    user: Optional[UserRead] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Registered email to receive password reset instructions",
        examples=["user@example.com"]
    )


class MessageResponse(BaseModel):
    message: str = Field(..., description="Response status message", examples=["Operation completed successfully."])
    otp: Optional[str] = Field(default=None, description="Generated 6-digit OTP verification code")


class ForgotPasswordResponse(MessageResponse):
    reset_token: Optional[str] = Field(
        None,
        description="Password reset token (available for testing and recovery convenience)",
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
