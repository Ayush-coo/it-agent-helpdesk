"""Tests for TicketService overview logic (updated for enterprise schema)."""
import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from app.models.ticket import (
    EscalationStatus,
    SeverityLevel,
    Ticket,
    TicketPriority,
    TicketStatus,
)
from app.models.user import UserRole
from app.services.ticket_service import TicketService


class FakeTicketRepository:
    def __init__(self, tickets: list[Ticket]) -> None:
        self._tickets = tickets

    async def list_all(self, session):
        return sorted(self._tickets, key=lambda ticket: ticket.created_at, reverse=True)

    async def list_by_requester(self, session, requester_id: str):
        return sorted(
            (ticket for ticket in self._tickets if ticket.requester_id == requester_id),
            key=lambda ticket: ticket.created_at,
            reverse=True,
        )

    async def add(self, session, ticket):
        self._tickets.append(ticket)
        return ticket

    async def get_by_id(self, session, ticket_id: str):
        return next((ticket for ticket in self._tickets if ticket.id == ticket_id), None)

    async def delete(self, session, ticket):
        self._tickets.remove(ticket)


def make_ticket(
    ticket_id: str,
    title: str,
    status: TicketStatus,
    requester_id: str,
    created_at: datetime,
    severity: SeverityLevel = SeverityLevel.P4_LOW,
) -> Ticket:
    ticket = Ticket(
        id=ticket_id,
        ticket_number=f"INC-{int(ticket_id):04d}",
        title=title,
        description=f"{title} description",
        status=status,
        priority=TicketPriority.MEDIUM,
        severity=severity,
        requester_id=requester_id,
        category="general",
        escalation_status=EscalationStatus.NONE,
    )
    ticket.created_at = created_at
    ticket.updated_at = created_at
    return ticket


def test_get_overview_groups_counts_and_recent_tickets() -> None:
    tickets = [
        make_ticket("3", "Password reset", TicketStatus.IN_PROGRESS, "user-1", datetime(2026, 8, 19, 11, 0, tzinfo=timezone.utc)),
        make_ticket("2", "Laptop repair", TicketStatus.RESOLVED, "user-2", datetime(2026, 8, 19, 10, 0, tzinfo=timezone.utc)),
        make_ticket("1", "VPN issue", TicketStatus.OPEN, "user-1", datetime(2026, 8, 19, 9, 0, tzinfo=timezone.utc)),
    ]
    service = TicketService(FakeTicketRepository(tickets))
    current_user = SimpleNamespace(id="agent-1", role=UserRole.AGENT)

    overview = asyncio.run(service.get_overview(SimpleNamespace(), current_user))

    assert overview.scope == "all tickets"
    assert overview.total == 3
    assert [item.count for item in overview.status_counts] == [1, 1, 0, 1, 0]
    assert [ticket.id for ticket in overview.recent_tickets] == ["3", "2", "1"]


def test_get_overview_limits_requesters_to_their_tickets() -> None:
    tickets = [
        make_ticket("1", "VPN issue", TicketStatus.OPEN, "user-1", datetime(2026, 8, 19, 9, 0, tzinfo=timezone.utc)),
        make_ticket("2", "Laptop repair", TicketStatus.RESOLVED, "user-2", datetime(2026, 8, 19, 10, 0, tzinfo=timezone.utc)),
    ]
    service = TicketService(FakeTicketRepository(tickets))
    current_user = SimpleNamespace(id="user-1", role=UserRole.USER)

    overview = asyncio.run(service.get_overview(SimpleNamespace(), current_user))

    assert overview.scope == "your tickets"
    assert overview.total == 1
    assert [ticket.id for ticket in overview.recent_tickets] == ["1"]