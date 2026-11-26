from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, max_length=36)
    ticket_id: str | None = None
    context: str | None = Field(default=None, max_length=4000)
    use_knowledge_base: bool = True
    action_confirmation: str | None = Field(default=None, pattern="^(confirm|cancel)$")
    otp: str | None = Field(default=None, max_length=32)


class ChatContextReference(BaseModel):
    id: str
    title: str
    source: str | None = None
    snippet: str
    score: float


class ChatTicket(BaseModel):
    id: str
    ticket_number: str
    status: str


class ChatResponse(BaseModel):
    reply: str
    model: str
    provider: str = "ollama"
    references: list[ChatContextReference] = Field(default_factory=list)
    conversation_id: str | None = None
    ticket: ChatTicket | None = None
    pending_action: str | None = None
    mock_otp: str | None = None