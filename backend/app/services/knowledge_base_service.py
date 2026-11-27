import logging
from datetime import datetime, timezone
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from app.core.config import settings
from app.schemas.knowledge_base import (
    KnowledgeBaseDocument,
    KnowledgeBaseIngestRequest,
    KnowledgeBaseSearchResult,
)

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self) -> None:
        self._embeddings = OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
        )
        self._store = Chroma(
            collection_name=settings.knowledge_collection_name,
            embedding_function=self._embeddings,
            persist_directory=settings.chroma_persist_directory,
        )

    def ingest(self, payload: KnowledgeBaseIngestRequest) -> KnowledgeBaseDocument:
        document_id = str(uuid4())
        created_at = datetime.now(timezone.utc)
        normalized_tags = [tag.strip().lower() for tag in payload.tags if tag.strip()]

        normalized_title = payload.title.strip()
        metadata = {
            "title": normalized_title,
            "source": payload.source.strip() if payload.source else None,
            "tags": "|".join(normalized_tags),
            "created_at": created_at.isoformat(),
        }

        self._store.add_texts(
            texts=[payload.content.strip()],
            metadatas=[metadata],
            ids=[document_id],
        )

        return KnowledgeBaseDocument(
            id=document_id,
            title=normalized_title,
            content=payload.content.strip(),
            source=metadata["source"],
            tags=normalized_tags,
            created_at=created_at,
        )

    def search(self, query: str, limit: int) -> list[KnowledgeBaseSearchResult]:
        clean_query = query.strip()
        if not clean_query:
            return []

        try:
            hits = self._store.similarity_search_with_relevance_scores(clean_query, k=limit)
        except Exception:
            logger.exception("Knowledge-base search failed")
            return []

        results: list[KnowledgeBaseSearchResult] = []

        for document, score in hits:
            metadata = document.metadata or {}
            title = str(metadata.get("title") or "Untitled knowledge item")
            source = metadata.get("source")
            tags_value = str(metadata.get("tags") or "")
            tags = [tag for tag in tags_value.split("|") if tag]

            results.append(
                KnowledgeBaseSearchResult(
                    id=str(document.id),
                    title=title,
                    source=str(source) if source else None,
                    tags=tags,
                    snippet=document.page_content[:320],
                    score=float(score),
                )
            )

        return [result for result in results if result.score >= settings.knowledge_min_score]