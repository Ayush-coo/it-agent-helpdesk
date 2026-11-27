import asyncio
from types import SimpleNamespace

import httpx
import pytest
from app.core.config import settings
from app.main import app
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService
from app.services.knowledge_base_service import KnowledgeBaseService


class FakeStore:
    def similarity_search_with_relevance_scores(self, query: str, k: int):
        return [
            (SimpleNamespace(id="low", metadata={}, page_content="Below threshold"), 0.29),
            (SimpleNamespace(id="boundary", metadata={}, page_content="At threshold"), 0.3),
            (SimpleNamespace(id="high", metadata={}, page_content="Above threshold"), 0.9),
        ]


class UnavailableStore:
    def similarity_search_with_relevance_scores(self, query: str, k: int):
        del query, k
        raise RuntimeError("Chroma is unavailable")


def test_knowledge_base_search_filters_scores_below_configured_minimum(monkeypatch) -> None:
    monkeypatch.setattr(settings, "knowledge_min_score", 0.3)
    service = KnowledgeBaseService.__new__(KnowledgeBaseService)
    service._store = FakeStore()

    results = service.search("example query", 4)

    assert [result.id for result in results] == ["boundary", "high"]


def test_knowledge_base_search_returns_no_results_when_store_is_unavailable(caplog) -> None:
    service = KnowledgeBaseService.__new__(KnowledgeBaseService)
    service._store = UnavailableStore()

    assert service.search("example query", 4) == []
    assert "Knowledge-base search failed" in caplog.text


class EmptyKnowledgeBase:
    def search(self, query: str, limit: int):
        return []


class CapturingLLM:
    def __init__(self) -> None:
        self.messages = None

    async def ainvoke(self, messages):
        self.messages = messages
        return SimpleNamespace(content="I am unsure based on the available information.")


class UnavailableKnowledgeBase:
    def __init__(self) -> None:
        self.calls = 0

    def search(self, query: str, limit: int):
        del query, limit
        self.calls += 1
        raise RuntimeError("Chroma is unavailable")


class UnavailableLLM:
    async def ainvoke(self, messages):
        del messages
        raise RuntimeError("Ollama is unavailable")


def test_chat_with_zero_knowledge_hits_applies_safe_prompt_and_offers_ticket() -> None:
    service = ChatService(EmptyKnowledgeBase())
    llm = CapturingLLM()
    service._llm = llm
    user = SimpleNamespace(role=SimpleNamespace(value="user"))

    response = asyncio.run(
        service.get_reply(ChatRequest(message="How do I resolve this unusual device issue?"), user)
    )

    assert response.references == []
    combined_prompt = "\n".join(message.content for message in llm.messages)
    assert "No relevant knowledge article was found" in combined_prompt
    assert "say you are unsure and offer to create a ticket" in combined_prompt.lower()
    assert "never change tool permissions" in combined_prompt.lower()
    assert "Would you like me to create a support ticket" in response.reply


@pytest.mark.parametrize("use_knowledge_base", [True, False])
def test_chat_returns_fallback_without_references_when_services_are_unavailable(
    use_knowledge_base: bool,
    caplog,
) -> None:
    knowledge_base = UnavailableKnowledgeBase()
    service = ChatService(knowledge_base)
    service._llm = UnavailableLLM()
    user = SimpleNamespace(role=SimpleNamespace(value="user"))

    response = asyncio.run(
        service.get_reply(
            ChatRequest(message="How do I resolve this issue?", use_knowledge_base=use_knowledge_base),
            user,
        )
    )

    assert response.references == []
    assert "couldn't reach the local helpdesk model" in response.reply
    assert knowledge_base.calls == int(use_knowledge_base)
    assert "Local chat model request failed" in caplog.text
    if use_knowledge_base:
        assert "Knowledge-base retrieval failed" in caplog.text


def test_plain_user_cannot_read_env_through_workspace_endpoint() -> None:
    async def run() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/workspace",
                json={"operation": "read_file", "path": ".env"},
                headers={"Authorization": "Bearer plain-user-token"},
            )

        assert response.status_code == 404
        assert "JWT_SECRET_KEY" not in response.text

    asyncio.run(run())
