import asyncio
from types import SimpleNamespace

from app.core.config import settings
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


def test_knowledge_base_search_filters_scores_below_configured_minimum(monkeypatch) -> None:
    monkeypatch.setattr(settings, "knowledge_min_score", 0.3)
    service = KnowledgeBaseService.__new__(KnowledgeBaseService)
    service._store = FakeStore()

    results = service.search("example query", 4)

    assert [result.id for result in results] == ["boundary", "high"]


class EmptyKnowledgeBase:
    def search(self, query: str, limit: int):
        return []


class CapturingLLM:
    def __init__(self) -> None:
        self.messages = None

    async def ainvoke(self, messages):
        self.messages = messages
        return SimpleNamespace(content="I am unsure based on the available information.")


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
