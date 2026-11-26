import json
from typing import Literal

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.integrations.identity import FakeIdentityProvider, IdentityProvider
from app.models.ticket import (
    EscalationStatus,
    SeverityLevel,
    Ticket,
    TicketComment,
    TicketEvent,
    TicketPriority,
    TicketStatus,
)
from app.models.user import User, UserRole
from app.repositories.ticket_repository import TicketRepository
from app.schemas.knowledge_base import KnowledgeBaseSearchResult
from app.services.knowledge_base_service import KnowledgeBaseService


class SearchKnowledgeBaseArgs(BaseModel):
    query: str = Field(min_length=1, max_length=4000)


class CreateTicketArgs(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    category: str = Field(default="general", max_length=120)
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    steps_tried: list[str] = Field(default_factory=list, max_length=20)


class GetTicketStatusArgs(BaseModel):
    ticket_id: str = Field(min_length=1, max_length=36)


class AddTicketCommentArgs(BaseModel):
    ticket_id: str = Field(min_length=1, max_length=36)
    body: str = Field(min_length=1, max_length=10000)
    is_internal: bool = False

    @field_validator("body")
    @classmethod
    def body_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Comment body cannot be blank.")
        return normalized


class EscalateToHumanArgs(BaseModel):
    ticket_id: str | None = Field(default=None, max_length=36)
    issue: str = Field(min_length=1, max_length=4000)
    steps_tried: list[str] = Field(default_factory=list, max_length=20)


class SensitiveActionArgs(BaseModel):
    target_user_id: str | None = Field(default=None, max_length=36)
    ticket_id: str | None = Field(default=None, max_length=36)


class AgentTools:
    def __init__(
        self,
        session: AsyncSession | None,
        current_user: User,
        knowledge_base: KnowledgeBaseService,
        identity_provider: IdentityProvider | None = None,
        references: list[KnowledgeBaseSearchResult] | None = None,
        conversation: list[dict[str, str]] | None = None,
    ) -> None:
        self.session = session
        self.current_user = current_user
        self.knowledge_base = knowledge_base
        self.identity_provider = identity_provider or FakeIdentityProvider()
        self.references = references or []
        self.conversation = conversation or []
        self.repository = TicketRepository()

    def as_langchain_tools(self) -> list[StructuredTool]:
        return [
            StructuredTool.from_function(
                coroutine=self.search_knowledge_base,
                name="search_knowledge_base",
                description="Search approved IT knowledge articles for relevant troubleshooting guidance.",
                args_schema=SearchKnowledgeBaseArgs,
            ),
            StructuredTool.from_function(
                coroutine=self.create_ticket,
                name="create_ticket",
                description="Create a support ticket after the user asks to create one.",
                args_schema=CreateTicketArgs,
            ),
            StructuredTool.from_function(
                coroutine=self.get_ticket_status,
                name="get_ticket_status",
                description="Get a ticket status. Requesters may only access their own tickets.",
                args_schema=GetTicketStatusArgs,
            ),
            StructuredTool.from_function(
                coroutine=self.add_ticket_comment,
                name="add_ticket_comment",
                description="Add a comment to an accessible ticket. Internal comments require staff.",
                args_schema=AddTicketCommentArgs,
            ),
            StructuredTool.from_function(
                coroutine=self.escalate_to_human,
                name="escalate_to_human",
                description="Escalate a ticket to a person with an internal handoff summary.",
                args_schema=EscalateToHumanArgs,
            ),
            StructuredTool.from_function(
                coroutine=self.reset_password,
                name="reset_password",
                description="Stage a password reset; it requires mock OTP and confirmation in the next turn.",
                args_schema=SensitiveActionArgs,
            ),
            StructuredTool.from_function(
                coroutine=self.unlock_account,
                name="unlock_account",
                description="Stage an account unlock; it requires mock OTP and confirmation in the next turn.",
                args_schema=SensitiveActionArgs,
            ),
        ]

    def _require_session(self) -> AsyncSession:
        if self.session is None:
            raise RuntimeError("Database session is required for this tool.")
        return self.session

    def _require_authenticated_role(self) -> None:
        role = getattr(self.current_user.role, "value", self.current_user.role)
        if role not in {item.value for item in UserRole}:
            raise PermissionError("This role is not permitted to use helpdesk tools.")

    def _can_access(self, ticket: Ticket) -> bool:
        return (
            self.current_user.role in {UserRole.AGENT, UserRole.ADMIN}
            or ticket.requester_id == self.current_user.id
        )

    async def search_knowledge_base(self, query: str) -> str:
        self._require_authenticated_role()
        results = await run_in_threadpool(
            self.knowledge_base.search,
            query,
            5,
        )
        self.references = results
        return json.dumps(
            [
                {
                    "id": item.id,
                    "title": item.title,
                    "source": item.source,
                    "snippet": item.snippet,
                    "score": item.score,
                }
                for item in results
            ]
        )

    async def create_ticket(
        self,
        title: str,
        description: str,
        category: str = "general",
        priority: str = "medium",
        steps_tried: list[str] | None = None,
    ) -> str:
        self._require_authenticated_role()
        session = self._require_session()
        normalized_steps = steps_tried or []
        content = description.strip()
        if normalized_steps:
            content += "\n\nSteps tried:\n" + "\n".join(f"- {step}" for step in normalized_steps)
        ticket = Ticket(
            ticket_number=await self.repository.allocate_ticket_number(session),
            title=title.strip(),
            description=content,
            status=TicketStatus.OPEN,
            priority=TicketPriority(priority),
            severity=SeverityLevel.P4_LOW,
            requester_id=self.current_user.id,
            category=category.strip() or "general",
            escalation_status=EscalationStatus.NONE,
        )
        await self.repository.add(session, ticket)
        session.add(
            TicketEvent(
                ticket_id=ticket.id,
                actor_id=self.current_user.id,
                type="created",
                new_value=ticket.title,
            )
        )
        await session.flush()
        return json.dumps({"ticket_id": ticket.id, "ticket_number": ticket.ticket_number, "status": ticket.status.value})

    async def get_ticket_status(self, ticket_id: str) -> str:
        self._require_authenticated_role()
        session = self._require_session()
        ticket = await self.repository.get_by_id(session, ticket_id)
        if ticket is None or not self._can_access(ticket):
            raise PermissionError("Ticket not found or you do not have permission to view it.")
        return json.dumps(
            {"ticket_id": ticket.id, "ticket_number": ticket.ticket_number, "status": ticket.status.value}
        )

    async def add_ticket_comment(self, ticket_id: str, body: str, is_internal: bool = False) -> str:
        self._require_authenticated_role()
        session = self._require_session()
        ticket = await self.repository.get_by_id(session, ticket_id)
        if ticket is None or not self._can_access(ticket):
            raise PermissionError("Ticket not found or you do not have permission to comment on it.")
        is_staff = self.current_user.role in {UserRole.AGENT, UserRole.ADMIN}
        if is_internal and not is_staff:
            raise PermissionError("Only agents and admins may add internal comments.")
        if not is_staff and ticket.status == TicketStatus.CLOSED:
            raise PermissionError("Closed tickets cannot be edited by requesters.")
        comment = TicketComment(
            ticket_id=ticket.id,
            author_id=self.current_user.id,
            body=body.strip(),
            is_internal=is_internal,
        )
        await self.repository.add_comment(session, comment)
        session.add(
            TicketEvent(
                ticket_id=ticket.id,
                actor_id=self.current_user.id,
                type="internal_comment_added" if is_internal else "comment_added",
                new_value=comment.id,
            )
        )
        await session.flush()
        return json.dumps({"comment_id": comment.id, "ticket_number": ticket.ticket_number})

    async def escalate_to_human(
        self,
        issue: str,
        steps_tried: list[str] | None = None,
        ticket_id: str | None = None,
    ) -> str:
        self._require_authenticated_role()
        session = self._require_session()
        ticket = await self.repository.get_by_id(session, ticket_id) if ticket_id else None
        if ticket_id and (ticket is None or not self._can_access(ticket)):
            raise PermissionError("Ticket not found or you do not have permission to escalate it.")
        if ticket is None:
            result = json.loads(
                await self.create_ticket(
                    title=issue[:200],
                    description=issue,
                    category="general",
                    priority="high",
                    steps_tried=steps_tried,
                )
            )
            ticket = await self.repository.get_by_id(session, result["ticket_id"])
        if ticket is None:
            raise RuntimeError("Unable to create the escalation ticket.")

        used_articles = [f"{item.title} ({item.id})" for item in self.references]
        summary = (
            f"Human handoff summary\nIssue: {issue}\n"
            f"Steps tried: {', '.join(steps_tried or []) or 'None recorded'}\n"
            f"Knowledge articles used: {', '.join(used_articles) or 'None'}"
        )
        comment = TicketComment(
            ticket_id=ticket.id,
            author_id=self.current_user.id,
            body=summary,
            is_internal=True,
        )
        await self.repository.add_comment(session, comment)
        session.add(
            TicketEvent(
                ticket_id=ticket.id,
                actor_id=self.current_user.id,
                type="escalated",
                new_value=comment.id,
            )
        )
        await session.flush()
        return json.dumps(
            {"ticket_id": ticket.id, "ticket_number": ticket.ticket_number, "status": ticket.status.value}
        )

    def validate_sensitive_target(self, args: dict[str, object]) -> str:
        self._require_authenticated_role()
        target_user_id = str(args.get("target_user_id") or self.current_user.id)
        if (
            target_user_id != self.current_user.id
            and self.current_user.role not in {UserRole.AGENT, UserRole.ADMIN}
        ):
            raise PermissionError("You may only perform account actions for your own account.")
        return target_user_id

    async def reset_password(self, target_user_id: str | None = None, ticket_id: str | None = None) -> str:
        del ticket_id
        self.validate_sensitive_target({"target_user_id": target_user_id})
        raise PermissionError("Password reset requires OTP verification and confirmation in the next turn.")

    async def unlock_account(self, target_user_id: str | None = None, ticket_id: str | None = None) -> str:
        del ticket_id
        self.validate_sensitive_target({"target_user_id": target_user_id})
        raise PermissionError("Account unlock requires OTP verification and confirmation in the next turn.")

    async def execute_sensitive(
        self,
        action: str,
        args: dict[str, object],
        *,
        otp_verified: bool,
        user_confirmed: bool,
    ) -> tuple[str, Ticket]:
        if action not in {"reset_password", "unlock_account"}:
            raise ValueError("Unsupported sensitive action.")
        if not otp_verified or not user_confirmed:
            raise PermissionError("Sensitive actions require verified OTP and explicit confirmation.")

        session = self._require_session()
        target_user_id = self.validate_sensitive_target(args)
        ticket_id = str(args.get("ticket_id") or "")
        ticket = await self.repository.get_by_id(session, ticket_id) if ticket_id else None
        if ticket is not None and not self._can_access(ticket):
            raise PermissionError("Ticket not found or you do not have permission to audit this action.")
        if ticket is None:
            ticket = Ticket(
                ticket_number=await self.repository.allocate_ticket_number(session),
                title="Password reset request" if action == "reset_password" else "Account unlock request",
                description="Sensitive account action requested and confirmed through chat.",
                status=TicketStatus.OPEN,
                priority=TicketPriority.MEDIUM,
                severity=SeverityLevel.P4_LOW,
                requester_id=self.current_user.id,
                category="access",
                escalation_status=EscalationStatus.NONE,
            )
            await self.repository.add(session, ticket)
            session.add(
                TicketEvent(
                    ticket_id=ticket.id,
                    actor_id=self.current_user.id,
                    type="created",
                    new_value=ticket.title,
                )
            )
        event = TicketEvent(
            ticket_id=ticket.id,
            actor_id=self.current_user.id,
            type=action,
            new_value=f"OTP verified; execution pending for user {target_user_id}",
        )
        session.add(event)
        await session.flush()
        event_id = event.id
        ticket_id = ticket.id
        await session.commit()

        operation = getattr(self.identity_provider, action)
        result = await operation(target_user_id)
        persisted_event = await session.get(TicketEvent, event_id)
        if persisted_event is None:
            raise RuntimeError("Sensitive action audit event was not persisted.")
        persisted_event.new_value = f"completed for user {target_user_id}"
        await session.flush()
        persisted_ticket = await self.repository.get_by_id(session, ticket_id)
        if persisted_ticket is None:
            raise RuntimeError("Sensitive action ticket was not persisted.")
        return result, persisted_ticket
