from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.knowledge_base import (
    KnowledgeBaseDocument,
    KnowledgeBaseIngestRequest,
    KnowledgeBaseSearchResponse,
)
from app.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter()


@router.post("/ingest", response_model=KnowledgeBaseDocument, dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
async def ingest_knowledge_item(payload: KnowledgeBaseIngestRequest, current_user: User = Depends(get_current_user)) -> KnowledgeBaseDocument:
    _ = current_user
    return KnowledgeBaseService().ingest(payload)


@router.get("/search", response_model=KnowledgeBaseSearchResponse)
async def search_knowledge_base(
    query: str = Query(min_length=2, max_length=500),
    k: int = Query(default=4, ge=1, le=10),
    current_user: User = Depends(get_current_user),
) -> KnowledgeBaseSearchResponse:
    _ = current_user
    results = KnowledgeBaseService().search(query, k)
    return KnowledgeBaseSearchResponse(query=query, results=results)