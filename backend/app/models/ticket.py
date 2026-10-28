from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, JSON
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
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


class SeverityLevel(str, Enum):
    """ITIL v4 severity levels for incident classification."""
    P1_CRITICAL = "P1"
    P2_HIGH = "P2"
    P3_MODERATE = "P3"
    P4_LOW = "P4"


class EscalationStatus(str, Enum):
    """State machine for Human-in-the-Loop escalation flow."""
    NONE = "none"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_RESOLVED = "auto_resolved"


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

    # --- NEW: ITIL v4 Severity ---
    severity = mapped_column(
        SAEnum(
            SeverityLevel,
            name="severity_level",
            native_enum=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=SeverityLevel.P4_LOW,
        nullable=False,
    )

    requester_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to_id = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category = mapped_column(String(120), nullable=True)

    # --- NEW: Antigravity Telemetry & Escalation ---
    diagnostic_trail = mapped_column(
        JSON,
        nullable=True,
        default=None,
        comment="Chain-of-thought diagnostic log: [{step, action, result, timestamp}, ...]",
    )
    affected_assets = mapped_column(
        JSON,
        nullable=True,
        default=None,
        comment="Extracted affected assets: device IDs, app names, user identifiers",
    )
    escalation_status = mapped_column(
        SAEnum(
            EscalationStatus,
            name="escalation_status",
            native_enum=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=EscalationStatus.NONE,
        nullable=False,
    )
    recommended_agent = mapped_column(String(100), nullable=True)
    runbook_result = mapped_column(
        JSON,
        nullable=True,
        default=None,
        comment="Result of automated runbook execution, if any",
    )
    service = mapped_column(String(120), nullable=True, index=True)
    site = mapped_column(String(120), nullable=True, index=True)
    subnet = mapped_column(String(120), nullable=True)
    asset_group = mapped_column(String(120), nullable=True)
    incident_id = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    incident_escalation_suppressed: Mapped[bool] = mapped_column(
        default=False, nullable=False, server_default="0"
    )

    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )