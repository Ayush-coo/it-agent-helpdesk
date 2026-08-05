from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_ON_USER = "waiting_on_user"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Ticket(Base):
    __tablename__ = "tickets"

    id = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title = mapped_column(String(200), nullable=False)
    description = mapped_column(Text, nullable=False)
    status = mapped_column(
        SAEnum(
            TicketStatus,
            name="ticket_status",
            native_enum=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=TicketStatus.OPEN,
        nullable=False,
    )
    priority = mapped_column(
        SAEnum(
            TicketPriority,
            name="ticket_priority",
            native_enum=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=TicketPriority.MEDIUM,
        nullable=False,
    )
    requester_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to_id = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category = mapped_column(String(120), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )