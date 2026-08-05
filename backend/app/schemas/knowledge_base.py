from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBaseIngestRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=10, max_length=20000)
    source: str | None = Field(default=None, max_length=300)
    tags: list[str] = Field(default_factory=list)


class KnowledgeBaseDocument(BaseModel):
    id: str
    title: str
    content: str
    source: str | None = None
    tags: list[str] = []
    created_at: datetime


class KnowledgeBaseSearchResult(BaseModel):
    id: str
    title: str
    source: str | None = None
    tags: list[str] = []
    snippet: str
    score: float


class KnowledgeBaseSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeBaseSearchResult]