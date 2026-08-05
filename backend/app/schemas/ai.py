from pydantic import BaseModel


class TriageRequest(BaseModel):
    description: str


class TriageResponse(BaseModel):
    priority: str
    category: str
    short_summary: str
    recommended_agent: str
    next_steps: list[str]
