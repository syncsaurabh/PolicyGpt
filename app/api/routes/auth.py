from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.dependencies import get_db
from app.core.security import create_access_token
from jose import JWTError, jwt
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    ResendOTPRequest,
    Token,
    VerifyOTPRequest,
)
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user in the PolicyGPT system.
    Creates account with email unverified and dispatches a 6-digit OTP code to the registered email.
    """
    new_user = AuthService.register_user(db=db, user_in=user_in)
    return new_user


@router.post("/verify-otp", response_model=Token)
def verify_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Verify 6-digit email OTP.
    Upon successful validation, marks user as verified and returns authenticated JWT access token.
    """
    user = AuthService.verify_otp(db=db, email=req.email, otp=req.otp)
    access_token = create_access_token(
        subject=user.id,
        role=user.role.value
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserRead.model_validate(user)
    )


@router.post("/resend-otp", response_model=MessageResponse)
def resend_otp(req: ResendOTPRequest, db: Session = Depends(get_db)):
    """
    Resend a 6-digit OTP code with 60-second cooldown rate-limiting.
    Invalidates any previous active OTP codes.
    """
    AuthService.resend_otp(db=db, email=req.email)
    return MessageResponse(message="A new verification code has been sent to your email.")


@router.post(
    "/login",
    response_model=Token,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "format": "email",
                                "example": "test@example.com",
                                "description": "Registered email address"
                            },
                            "password": {
                                "type": "string",
                                "example": "Test@1234",
                                "description": "Account password"
                            }
                        },
                        "required": ["email", "password"]
                    }
                }
            }
        }
    }
)
async def login(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate user with email and password, returning a signed JWT access token.
    Blocks login access if the user email has not been verified.
    """
    email = None
    password = None

    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
            email = body.get("email") or body.get("username")
            password = body.get("password")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
    else:
        # Check form data (e.g. urlencoded form or form-data)
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")

    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email/username and password are required"
        )

    user = AuthService.authenticate_user(db=db, email=email, password=password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Login protection: Require email verification
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before signing in."
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserRead.model_validate(user)
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiate a password reset workflow (Step 1 of password recovery).
    Generates a secure password-reset token if the email exists, without leaking account existence.
    In development mode, the reset token is returned in the response for testing convenience.
    """
    reset_token = AuthService.request_password_reset(db=db, email=req.email)
    
    response_msg = "If this email is registered, password reset instructions have been sent."
    if settings.ENVIRONMENT == "development" and reset_token:
        response_msg += f" (Dev token: {reset_token})"

    return ForgotPasswordResponse(
        message=response_msg,
        reset_token=reset_token if settings.ENVIRONMENT == "development" else None
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Complete password reset workflow (Step 2 of password recovery).
    Requires the password-reset token obtained from /forgot-password.
    """
    try:
        unverified_payload = jwt.decode(
            req.token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        if unverified_payload.get("type") == "access":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type: Received an access token from /login, but this endpoint requires a password reset token from /forgot-password."
            )
    except JWTError:
        pass

    success = AuthService.reset_password(
        db=db,
        token=req.token,
        new_password=req.new_password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or unrecognized password reset token"
        )

    return MessageResponse(message="Password has been successfully reset. You may now log in.")
