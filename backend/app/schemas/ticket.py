from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ticket import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    priority: TicketPriority = TicketPriority.MEDIUM
    category: str | None = Field(default=None, max_length=120)


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_to_id: str | None = None
    category: str | None = Field(default=None, max_length=120)


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    requester_id: str
    assigned_to_id: str | None = None
    category: str | None = None
    created_at: datetime
    updated_at: datetime
