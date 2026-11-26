from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    full_name = mapped_column(String(120), nullable=True)
    email = mapped_column(String(255), unique=True, nullable=False)
    password_hash = mapped_column(String(255), nullable=False)
    role = mapped_column(
        SAEnum(
            UserRole,
            name="user_role",
            native_enum=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=UserRole.USER,
        nullable=False,
    )
    is_active = mapped_column(Boolean, default=True, nullable=False)
    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
