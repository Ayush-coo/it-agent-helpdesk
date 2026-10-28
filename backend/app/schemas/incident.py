from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.incident import IncidentStatus


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    status: IncidentStatus
    service: str | None
    site: str | None
    subnet: str | None
    asset_group: str | None
    member_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    root_cause_hypothesis: str | None
    suggested_owner: str | None
    timeline: list[dict[str, Any]] | None
    created_at: datetime
    updated_at: datetime
