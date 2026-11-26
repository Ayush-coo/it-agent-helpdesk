from typing import Any

from pydantic import BaseModel


class TriageRequest(BaseModel):
    description: str


class TriageResponse(BaseModel):
    priority: str
    severity: str
    category: str
    short_summary: str
    next_steps: list[str]
    affected_assets: list[str] = []
    diagnostic_trail: list[dict[str, Any]] = []
    requires_escalation: bool = False


class AIStatusResponse(BaseModel):
    provider: str = "ollama"
    model: str
    available: bool
    detail: str
