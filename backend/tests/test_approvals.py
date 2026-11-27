import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.approval import ApprovalRequest
from app.models.ticket import EscalationStatus, SeverityLevel, Ticket, TicketPriority, TicketStatus
from app.models.user import UserRole
from app.schemas.ticket import EscalationAction
from app.services.ticket_service import TicketService


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeSession:
    def __init__(self, approval_request):
        self.approval_request = approval_request
        self.added = []

    def add(self, item):
        self.added.append(item)

    async def execute(self, _statement):
        return FakeResult(self.approval_request)

    async def commit(self):
        return None

    async def refresh(self, _item):
        return None


class FakeTicketRepository:
    def __init__(self, ticket):
        self.ticket = ticket

    async def get_by_id(self, _session, _ticket_id):
        return self.ticket


def _pending_ticket():
    ticket = Ticket(
        id="ticket-1",
        ticket_number="INC-0001",
        title="Suspected phishing",
        description="A phishing link was clicked",
        status=TicketStatus.OPEN,
        priority=TicketPriority.URGENT,
        severity=SeverityLevel.P1_CRITICAL,
        requester_id="requester-1",
        escalation_status=EscalationStatus.PENDING_REVIEW,
    )
    ticket.diagnostic_trail = []
    ticket.created_at = datetime.now(timezone.utc)
    ticket.updated_at = ticket.created_at
    return ticket


def test_requester_cannot_approve_own_escalation() -> None:
    async def run():
        service = TicketService(FakeTicketRepository(_pending_ticket()))
        session = FakeSession(ApprovalRequest(
            id="approval-1",
            ticket_id="ticket-1",
            requester_id="requester-1",
            status="pending",
        ))
        requester = SimpleNamespace(id="requester-1", role=UserRole.AGENT)

        with pytest.raises(ValueError, match="cannot approve or reject their own"):
            await service.handle_escalation(
                session,
                "ticket-1",
                EscalationAction(action="approve"),
                requester,
            )

    asyncio.run(run())


def test_separate_agent_decision_is_persisted() -> None:
    async def run():
        approval = ApprovalRequest(
            id="approval-1",
            ticket_id="ticket-1",
            requester_id="requester-1",
            status="pending",
        )
        ticket = _pending_ticket()
        session = FakeSession(approval)
        agent = SimpleNamespace(id="agent-1", email="agent@example.com", role=UserRole.AGENT)

        result = await TicketService(FakeTicketRepository(ticket)).handle_escalation(
            session,
            "ticket-1",
            EscalationAction(action="approve", reason="Verified incident"),
            agent,
        )

        assert result is ticket
        assert approval.status == "approved"
        assert approval.approver_id == agent.id
        assert approval.reason == "Verified incident"
        assert approval.decided_at is not None
        assert any(item.type == "approval_approved" for item in session.added)

    asyncio.run(run())
