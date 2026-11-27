import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from app.models.ticket import EscalationStatus, SeverityLevel, Ticket, TicketPriority, TicketStatus
from app.models.user import UserRole
from app.services.ticket_service import TicketService


class FakeSession:
    def __init__(self):
        self.added = []

    def add(self, item):
        self.added.append(item)

    async def commit(self):
        return None

    async def refresh(self, _item):
        return None


class FakeTicketRepository:
    def __init__(self, ticket):
        self.ticket = ticket

    async def get_by_id(self, _session, _ticket_id):
        return self.ticket


def test_denied_dry_run_is_reported_as_denied_not_simulated() -> None:
    async def run():
        now = datetime.now(timezone.utc)
        ticket = Ticket(
            id="ticket-1",
            ticket_number="INC-0001",
            title="Health check",
            description="Check endpoint health",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            severity=SeverityLevel.P4_LOW,
            requester_id="requester-1",
            escalation_status=EscalationStatus.NONE,
        )
        ticket.created_at = now
        ticket.updated_at = now
        user = SimpleNamespace(id="agent-1", role=UserRole.AGENT)
        result = await TicketService(FakeTicketRepository(ticket)).execute_ticket_runbook(
            FakeSession(),
            ticket.id,
            "system_health_check",
            {},
            user,
            dry_run=True,
        )

        assert result.runbook_result["status"] == "blocked"
        assert result.runbook_result["actions"][0].startswith("Denied:")
        assert result.runbook_result["details"]["policy_decision"] == "deny"

    asyncio.run(run())
