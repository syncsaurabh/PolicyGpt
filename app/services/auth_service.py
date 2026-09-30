from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password, create_password_reset_token, verify_password_reset_token


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
    def register_user(db: Session, user_in: UserCreate) -> User:
        """Register a new user after verifying uniqueness and hashing password."""
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
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

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
