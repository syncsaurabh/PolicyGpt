from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import secrets
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.user import User, UserRole
from app.models.otp import EmailOTP
from app.schemas.user import UserCreate
from app.core.security import (
    get_password_hash,
    verify_password,
    create_password_reset_token,
    verify_password_reset_token,
)
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


def generate_otp() -> str:
    """Generate a cryptographically secure 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000}"


def hash_otp(otp: str) -> str:
    """Generate a secure HMAC-SHA256 hash of the OTP using server SECRET_KEY."""
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        otp.strip().encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def verify_otp_hash(otp: str, hashed: str) -> bool:
    """Validate OTP against stored hash in constant time."""
    expected = hash_otp(otp)
    return hmac.compare_digest(expected, hashed)


class AuthService:
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Fetch a user by case-insensitive email."""
        return db.query(User).filter(User.email.ilike(email.strip())).first()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Fetch a user by primary key."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def send_otp_email(email: str, name: str, otp: str) -> None:
        """Send formatted PolicyGPT email OTP verification code."""
        subject = "Your PolicyGPT Verification Code"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 0; }}
            .container {{ max-width: 540px; margin: 30px auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .header {{ background: linear-gradient(135deg, #1d4ed8, #2563eb); padding: 28px 24px; text-align: center; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }}
            .header p {{ margin: 6px 0 0; font-size: 13px; opacity: 0.9; }}
            .content {{ padding: 32px 28px; }}
            .greeting {{ font-size: 16px; font-weight: 600; color: #0f172a; margin-bottom: 12px; }}
            .desc {{ font-size: 14px; color: #475569; line-height: 1.6; margin-bottom: 24px; }}
            .otp-box {{ background: #f1f5f9; border: 2px dashed #cbd5e1; border-radius: 10px; padding: 18px; text-align: center; margin: 24px 0; }}
            .otp-code {{ font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #1d4ed8; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }}
            .expiry-note {{ font-size: 13px; color: #64748b; margin-top: 8px; font-weight: 500; }}
            .security-box {{ background: #eff6ff; border-left: 4px solid #2563eb; padding: 12px 16px; border-radius: 4px; font-size: 13px; color: #1e40af; margin-top: 24px; }}
            .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 24px; text-align: center; font-size: 12px; color: #94a3b8; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>PolicyGPT</h1>
              <p>Government Policy & Public Scheme Intelligence Platform</p>
            </div>
            <div class="content">
              <div class="greeting">Hello {name or 'Citizen'},</div>
              <p class="desc">
                Thank you for creating an account on PolicyGPT. Please use the 6-digit verification code below to complete your email verification:
              </p>
              <div class="otp-box">
                <div class="otp-code">{otp}</div>
                <div class="expiry-note">This code will expire in <strong>5 minutes</strong>.</div>
              </div>
              <div class="security-box">
                <strong>Security Notice:</strong> Never share this code with anyone. PolicyGPT officials will never ask for your verification code. If you did not request this, please disregard this email.
              </div>
            </div>
            <div class="footer">
              &copy; 2026 PolicyGPT Platform. Secure Government Intelligence.
            </div>
          </div>
        </body>
        </html>
        """

        text_content = f"""
PolicyGPT Email Verification

Hello {name or 'Citizen'},

Your 6-digit verification code is: {otp}

This code is valid for 5 minutes. Please enter it on the email verification screen to activate your account.

If you did not create a PolicyGPT account, you can safely ignore this email.
        """.strip()

        EmailService.send_email_background(
            to_email=email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    @staticmethod
    def generate_and_send_otp(db: Session, user: User) -> str:
        """Generate secure 6-digit OTP, invalidate previous ones, store hash, and dispatch email."""
        # Invalidate any existing unused OTPs for this email
        db.query(EmailOTP).filter(
            EmailOTP.email.ilike(user.email),
            EmailOTP.is_used == False
        ).update({"is_used": True}, synchronize_session=False)

        otp = generate_otp()
        otp_hashed = hash_otp(otp)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        otp_record = EmailOTP(
            user_id=user.id,
            email=user.email.lower().strip(),
            otp_hash=otp_hashed,
            attempts=0,
            is_used=False,
            expires_at=expires_at,
        )
        db.add(otp_record)
        db.commit()

        # Dispatch email asynchronously
        AuthService.send_otp_email(
            email=user.email,
            name=user.name,
            otp=otp
        )

        return otp

    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        """Register a new user with is_verified=False and send OTP."""
        existing_user = AuthService.get_by_email(db, user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )

        role = user_in.role if isinstance(user_in.role, UserRole) else UserRole.from_string(str(user_in.role))

        db_user = User(
            name=user_in.name.strip(),
            email=user_in.email.strip().lower(),
            password_hash=get_password_hash(user_in.password),
            role=role,
            is_active=True,
            is_verified=False,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Generate and dispatch OTP
        AuthService.generate_and_send_otp(db, db_user)

        return db_user

    @staticmethod
    def verify_otp(db: Session, email: str, otp: str) -> User:
        """Validate 6-digit OTP against stored hash with expiry, attempt limits, and single-use enforcement."""
        user = AuthService.get_by_email(db, email)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account not found or is currently inactive."
            )

        if user.is_verified:
            # Already verified
            return user

        # Retrieve the latest active OTP for this email
        otp_record = db.query(EmailOTP).filter(
            EmailOTP.email.ilike(email.strip()),
            EmailOTP.is_used == False
        ).order_by(EmailOTP.created_at.desc()).first()

        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active verification code found for this email. Please request a new code."
            )

        # Check maximum verification attempts (max 5)
        if otp_record.attempts >= 5:
            otp_record.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum verification attempts exceeded. Please request a new code."
            )

        # Check expiration (5 minutes)
        now = datetime.now(timezone.utc)
        exp = otp_record.expires_at if otp_record.expires_at.tzinfo else otp_record.expires_at.replace(tzinfo=timezone.utc)
        if now > exp:
            otp_record.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your verification code has expired. Please request a new code."
            )

        # Check OTP hash match
        otp_record.attempts += 1
        if not verify_otp_hash(otp, otp_record.otp_hash):
            db.commit()
            remaining = 5 - otp_record.attempts
            if remaining > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid verification code. {remaining} attempt{'s' if remaining > 1 else ''} remaining."
                )
            else:
                otp_record.is_used = True
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum verification attempts exceeded. Please request a new code."
                )

        # Successful verification
        otp_record.is_used = True
        user.is_verified = True
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def resend_otp(db: Session, email: str) -> bool:
        """Resend OTP with 60-second rate-limiting cooldown and invalidation of previous codes."""
        user = AuthService.get_by_email(db, email)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found with this email address."
            )

        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your email is already verified. You may sign in directly."
            )

        # Enforce 60-second cooldown from the most recent OTP generation
        recent_otp = db.query(EmailOTP).filter(
            EmailOTP.email.ilike(email.strip())
        ).order_by(EmailOTP.created_at.desc()).first()

        if recent_otp and recent_otp.created_at:
            now = datetime.now(timezone.utc)
            created = recent_otp.created_at if recent_otp.created_at.tzinfo else recent_otp.created_at.replace(tzinfo=timezone.utc)
            elapsed_seconds = (now - created).total_seconds()
            if elapsed_seconds < 60:
                wait_sec = int(60 - elapsed_seconds)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Please wait {wait_sec} seconds before requesting another verification code."
                )

        # Generate and dispatch new OTP
        AuthService.generate_and_send_otp(db, user)
        return True

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Verify user credentials and return the user if valid and active."""
        user = AuthService.get_by_email(db, email)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def request_password_reset(db: Session, email: str) -> Optional[str]:
        """Generate a password reset token for registered, active users."""
        user = AuthService.get_by_email(db, email)
        if not user or not user.is_active:
            return None
        return create_password_reset_token(user.email)

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        """Verify token and update the user password."""
        email = verify_password_reset_token(token)
        if not email:
            return False

        user = AuthService.get_by_email(db, email)
        if not user or not user.is_active:
            return False

        user.password_hash = get_password_hash(new_password)
        db.commit()
        return True
