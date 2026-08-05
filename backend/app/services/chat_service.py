from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.models.user import User
from app.schemas.chat import ChatContextReference, ChatRequest, ChatResponse
from app.services.knowledge_base_service import KnowledgeBaseService


class ChatService:
    def __init__(self) -> None:
        self._llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=settings.ollama_temperature,
            timeout=settings.ollama_timeout_seconds,
        )
        self._knowledge_base = KnowledgeBaseService()
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are an IT helpdesk assistant for an enterprise support team. "
                        "Provide concise, practical troubleshooting steps. "
                        "If data is missing, ask clarifying questions. "
                        "Do not claim to perform actions you cannot execute. "
                        "If a knowledge-base excerpt is provided, prioritize it and mention uncertainty when needed."
                    ),
                ),
                (
                    "human",
                    (
                        "User role: {role}\n"
                        "User email: {email}\n"
                        "Ticket ID: {ticket_id}\n"
                        "Extra context: {context}\n\n"
                        "Knowledge base excerpts:\n{knowledge_context}\n\n"
                        "Question:\n{message}"
                    ),
                ),
            ]
        )

    async def get_reply(self, payload: ChatRequest, current_user: User) -> ChatResponse:
        ticket_id = payload.ticket_id or "not_provided"
        context = payload.context or "none"
        references: list[ChatContextReference] = []
        knowledge_context = "none"

        if payload.use_knowledge_base:
            search_results = self._knowledge_base.search(payload.message.strip(), settings.knowledge_retrieval_k)
            if search_results:
                references = [
                    ChatContextReference(
                        id=result.id,
                        title=result.title,
                        source=result.source,
                        snippet=result.snippet,
                        score=result.score,
                    )
                    for result in search_results
                ]
                knowledge_context = "\n\n".join(
                    f"[{idx}] {item.title} (score={item.score:.3f})\n{item.snippet}"
                    for idx, item in enumerate(references, start=1)
                )

        try:
            messages = self._prompt.format_messages(
                role=current_user.role.value,
                email=current_user.email,
                ticket_id=ticket_id,
                context=context,
                knowledge_context=knowledge_context,
                message=payload.message.strip(),
            )
            response = await self._llm.ainvoke(messages)
        except Exception as exc:
            raise RuntimeError(
                "AI service is unavailable. Ensure Ollama is running and the configured model is pulled."
            ) from exc

        content = response.content if isinstance(response.content, str) else str(response.content)
        return ChatResponse(reply=content.strip(), model=settings.ollama_model, references=references)