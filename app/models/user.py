from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
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

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        SQLEnum(UserRole, name="user_role_enum", native_enum=False),
        nullable=False,
        default=UserRole.CITIZEN
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
