from enum import Enum
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class IncidentStatus(str, Enum):
    PROBABLE = "probable"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"


class Incident(Base):
    __tablename__ = "incidents"

    id = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title = mapped_column(String(200), nullable=False)
    status = mapped_column(
        SAEnum(
            IncidentStatus,
            name="incident_status",
            native_enum=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=IncidentStatus.PROBABLE,
        nullable=False,
    )
    service = mapped_column(String(120), nullable=True)
    site = mapped_column(String(120), nullable=True)
    subnet = mapped_column(String(120), nullable=True)
    asset_group = mapped_column(String(120), nullable=True)
    member_count = mapped_column(Integer, nullable=False, default=0)
    first_seen_at = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at = mapped_column(DateTime(timezone=True), nullable=False)
    root_cause_hypothesis = mapped_column(Text, nullable=True)
    suggested_owner = mapped_column(String(120), nullable=True)
    timeline = mapped_column(JSON, nullable=True, default=list)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class IncidentTicket(Base):
    __tablename__ = "incident_tickets"

    incident_id = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True
    )
    ticket_id = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True
    )
    similarity = mapped_column(Float, nullable=False, default=0)
    linked_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
