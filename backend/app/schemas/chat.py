from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    ticket_id: str | None = None
    context: str | None = Field(default=None, max_length=4000)
    use_knowledge_base: bool = True


class ChatContextReference(BaseModel):
    id: str
    title: str
    source: str | None = None
    snippet: str
    score: float


class ChatResponse(BaseModel):
    reply: str
    model: str
    provider: str = "ollama"
    references: list[ChatContextReference] = []