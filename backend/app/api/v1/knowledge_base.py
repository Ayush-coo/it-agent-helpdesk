from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.dependencies import get_current_user, get_knowledge_base_service, require_roles
from app.db.session import get_db
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.schemas.knowledge_base import (
    KnowledgeBaseDocument,
    KnowledgeBaseIngestRequest,
    KnowledgeBaseSearchResponse,
)
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.knowledge_debt import detect_knowledge_debt, draft_knowledge_article

router = APIRouter()


class KnowledgeDebtApproval(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=20, max_length=10000)
    source: str = Field(default="knowledge-debt-loop", max_length=120)
    tags: list[str] = Field(default_factory=list)


@router.get("/debt", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
async def list_knowledge_debt(
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    knowledge_base: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> list[dict]:
    tickets = list((await session.execute(select(Ticket).where(Ticket.status == TicketStatus.RESOLVED))).scalars().all())
    clusters = await run_in_threadpool(detect_knowledge_debt, tickets, knowledge_base)
    drafts = [await draft_knowledge_article(cluster) for cluster in clusters]
    return [{"cluster": cluster.__dict__, "draft": draft.__dict__} for cluster, draft in zip(clusters, drafts, strict=True)]


@router.post("/debt/approve", response_model=KnowledgeBaseDocument, dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
async def approve_knowledge_debt(
    payload: KnowledgeDebtApproval,
    _current_user: User = Depends(get_current_user),
    knowledge_base: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBaseDocument:
    document = KnowledgeBaseIngestRequest(
        title=payload.title,
        content=payload.content,
        source=payload.source,
        tags=payload.tags,
    )
    return await run_in_threadpool(
        knowledge_base.ingest,
        document,
    )


@router.post("/ingest", response_model=KnowledgeBaseDocument, dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
async def ingest_knowledge_item(
    payload: KnowledgeBaseIngestRequest,
    current_user: User = Depends(get_current_user),
    knowledge_base: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBaseDocument:
    _ = current_user
    return await run_in_threadpool(knowledge_base.ingest, payload)


@router.get("/search", response_model=KnowledgeBaseSearchResponse)
async def search_knowledge_base(
    query: str = Query(min_length=2, max_length=500),
    k: int = Query(default=4, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    knowledge_base: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBaseSearchResponse:
    _ = current_user
    results = await run_in_threadpool(knowledge_base.search, query, k)
    return KnowledgeBaseSearchResponse(query=query, results=results)