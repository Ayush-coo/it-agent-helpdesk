import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.ticket import (
    EscalationStatus,
    SeverityLevel,
    Ticket,
    TicketComment,
    TicketPriority,
    TicketStatus,
)
from app.models.user import UserRole
from app.schemas.ticket import TicketCommentCreate, TicketUpdate
from app.services.ticket_service import TicketService


class FakeResult:
    def scalar_one_or_none(self):
        return None

    def scalars(self):
        return self

    def all(self):
        return []


class FakeSession:
    def __init__(self):
        self.added = []

    def add(self, item):
        self.added.append(item)

    async def execute(self, _statement):
        return FakeResult()

    async def flush(self):
        return None

    async def commit(self):
        return None

    async def refresh(self, _item):
        return None


class FakeTicketRepository:
    def __init__(self, ticket):
        self.ticket = ticket
        self.comments = []

    async def get_by_id(self, _session, _ticket_id):
        return self.ticket

    async def list_comments(self, _session, _ticket_id, include_internal):
        return [
            comment for comment in self.comments
            if include_internal or not comment.is_internal
        ]


def make_ticket(status=TicketStatus.OPEN):
    ticket = Ticket(
        id="ticket-1",
        ticket_number="INC-0001",
        title="VPN access",
        description="Unable to connect to the company VPN.",
        status=status,
        priority=TicketPriority.MEDIUM,
        severity=SeverityLevel.P4_LOW,
        requester_id="requester-1",
        escalation_status=EscalationStatus.NONE,
    )
    ticket.created_at = datetime.now(timezone.utc)
    ticket.updated_at = ticket.created_at
    return ticket


def test_status_transition_allows_progress_and_reopen_but_rejects_skips():
    async def run():
        ticket = make_ticket()
        service = TicketService(FakeTicketRepository(ticket))
        agent = SimpleNamespace(id="agent-1", role=UserRole.AGENT)
        session = FakeSession()

        with pytest.raises(ValueError, match="Cannot move"):
            await service.update_ticket(
                session, ticket.id, TicketUpdate(status=TicketStatus.CLOSED), agent
            )

        updated = await service.update_ticket(
            session, ticket.id, TicketUpdate(status=TicketStatus.IN_PROGRESS), agent
        )
        assert updated.status == TicketStatus.IN_PROGRESS
        assert any(
            getattr(item, "type", None) == "status_changed" for item in session.added
        )

        ticket.status = TicketStatus.RESOLVED
        reopened = await service.update_ticket(
            session, ticket.id, TicketUpdate(status=TicketStatus.IN_PROGRESS), agent
        )
        assert reopened.status == TicketStatus.IN_PROGRESS

    asyncio.run(run())


def test_requesters_cannot_change_workflow_fields_or_edit_closed_tickets():
    async def run():
        ticket = make_ticket()
        service = TicketService(FakeTicketRepository(ticket))
        requester = SimpleNamespace(id="requester-1", role=UserRole.USER)
        session = FakeSession()

        with pytest.raises(PermissionError, match="workflow fields"):
            await service.update_ticket(
                session, ticket.id, TicketUpdate(status=TicketStatus.IN_PROGRESS), requester
            )

        ticket.status = TicketStatus.CLOSED
        with pytest.raises(PermissionError, match="Closed tickets"):
            await service.update_ticket(
                session, ticket.id, TicketUpdate(title="Updated issue"), requester
            )

    asyncio.run(run())


def test_agent_cannot_assign_ticket_to_a_requester(monkeypatch):
    async def run():
        ticket = make_ticket()
        service = TicketService(FakeTicketRepository(ticket))
        agent = SimpleNamespace(id="agent-1", role=UserRole.AGENT)

        async def get_requester(_repository, _session, _user_id):
            return SimpleNamespace(
                id="requester-2",
                role=UserRole.USER,
                is_active=True,
            )

        monkeypatch.setattr(
            "app.services.ticket_service.UserRepository.get_by_id", get_requester
        )
        with pytest.raises(ValueError, match="active agents or admins"):
            await service.update_ticket(
                FakeSession(),
                ticket.id,
                TicketUpdate(assigned_to_id="requester-2"),
                agent,
            )

    asyncio.run(run())


def test_internal_comments_are_visible_to_staff_only():
    async def run():
        ticket = make_ticket()
        repository = FakeTicketRepository(ticket)
        repository.comments = [
            TicketComment(id="public", ticket_id=ticket.id, author_id="agent-1", body="Update", is_internal=False),
            TicketComment(id="internal", ticket_id=ticket.id, author_id="agent-1", body="Internal note", is_internal=True),
        ]
        service = TicketService(repository)
        requester = SimpleNamespace(id="requester-1", role=UserRole.USER)
        agent = SimpleNamespace(id="agent-1", role=UserRole.AGENT)

        public_comments = await service.list_comments(FakeSession(), ticket.id, requester)
        staff_comments = await service.list_comments(FakeSession(), ticket.id, agent)
        assert [comment.id for comment in public_comments] == ["public"]
        assert [comment.id for comment in staff_comments] == ["public", "internal"]

        with pytest.raises(PermissionError, match="internal comments"):
            await service.add_comment(
                FakeSession(),
                ticket.id,
                TicketCommentCreate(body="Private", is_internal=True),
                requester,
            )

    asyncio.run(run())
