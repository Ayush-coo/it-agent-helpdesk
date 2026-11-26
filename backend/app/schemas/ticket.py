from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.ticket import (
    EscalationStatus,
    SeverityLevel,
    TicketPriority,
    TicketStatus,
)


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    priority: TicketPriority = TicketPriority.MEDIUM
    category: str | None = Field(default=None, max_length=120)
    service: str | None = Field(default=None, max_length=120)
    site: str | None = Field(default=None, max_length=120)
    subnet: str | None = Field(default=None, max_length=120)
    asset_group: str | None = Field(default=None, max_length=120)


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    severity: SeverityLevel | None = None
    assigned_to_id: str | None = None
    category: str | None = Field(default=None, max_length=120)
    escalation_status: EscalationStatus | None = None


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_number: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    severity: SeverityLevel
    requester_id: str
    assigned_to_id: str | None = None
    category: str | None = None
    diagnostic_trail: list[dict[str, Any]] | None = None
    affected_assets: list[str] | None = None
    escalation_status: EscalationStatus = EscalationStatus.NONE
    runbook_result: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class TicketCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)
    is_internal: bool = False

    @field_validator("body")
    @classmethod
    def body_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Comment body cannot be blank")
        return normalized


class TicketCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    author_id: str
    body: str
    is_internal: bool
    created_at: datetime


class TicketEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    actor_id: str | None
    type: str
    old_value: str | None
    new_value: str | None
    created_at: datetime


class TicketStatusCount(BaseModel):
    status: TicketStatus
    count: int


class TicketOverview(BaseModel):
    scope: str
    total: int
    status_counts: list[TicketStatusCount]
    recent_tickets: list[TicketRead]
    refreshed_at: datetime


# --- NEW: Escalation schemas ---

class EscalationAction(BaseModel):
    """Payload for approving or rejecting a P1/P2 escalation."""
    action: str = Field(description="Must be 'approve' or 'reject'")
    reason: str | None = Field(default=None, max_length=500)


class EscalationSummary(BaseModel):
    """Structured HITL handoff summary for senior engineers."""
    model_config = ConfigDict(from_attributes=True)

    ticket_id: str
    title: str
    severity: SeverityLevel
    priority: TicketPriority
    category: str | None = None
    escalation_status: EscalationStatus
    affected_assets: list[str] | None = None
    diagnostic_trail: list[dict[str, Any]] | None = None
    root_cause_hypothesis: str | None = None
    recommended_actions: list[str] | None = None
