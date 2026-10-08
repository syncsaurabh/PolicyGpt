from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.database import Base


class UserRole(str, Enum):
    ADMINISTRATOR = "ADMINISTRATOR"
    GOVERNMENT_OFFICIAL = "GOVERNMENT_OFFICIAL"
    CITIZEN = "CITIZEN"
    RESEARCHER = "RESEARCHER"
    ORGANIZATION = "ORGANIZATION"
    GUEST_USER = "GUEST_USER"

    @classmethod
    def from_string(cls, value: str) -> "UserRole":
        """Normalize string representations (e.g. from frontend labels) to enum."""
        if not value:
            return cls.CITIZEN
        clean = value.strip().upper().replace(" ", "_")
        if clean in cls.__members__:
            return cls[clean]
        # Common frontend mappings
        mapping = {
            "ADMIN": cls.ADMINISTRATOR,
            "ADMINISTRATOR": cls.ADMINISTRATOR,
            "GOVERNMENT": cls.GOVERNMENT_OFFICIAL,
            "GOVERNMENT_OFFICIAL": cls.GOVERNMENT_OFFICIAL,
            "CITIZEN": cls.CITIZEN,
            "RESEARCHER": cls.RESEARCHER,
            "ORGANIZATION": cls.ORGANIZATION,
            "GUEST": cls.GUEST_USER,
            "GUEST_USER": cls.GUEST_USER,
        }
        return mapping.get(clean, cls.CITIZEN)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role_enum", native_enum=False),
        nullable=False,
        default=UserRole.CITIZEN
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
