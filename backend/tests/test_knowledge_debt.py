import asyncio
from types import SimpleNamespace

from app.models.ticket import TicketStatus
from app.services.knowledge_debt import (
    detect_knowledge_debt,
    draft_knowledge_article,
    knowledge_coverage_report,
)


class FakeSearcher:
    def search(self, query: str, limit: int):
        return [] if "vpn" in query.lower() else [SimpleNamespace(score=0.9)]


def test_resolved_tickets_without_kb_matches_form_debt_cluster() -> None:
    tickets = [
        SimpleNamespace(id="1", status=TicketStatus.RESOLVED, category="network", description="VPN certificate loop"),
        SimpleNamespace(id="2", status=TicketStatus.RESOLVED, category="network", description="VPN certificate loop"),
        SimpleNamespace(id="3", status=TicketStatus.OPEN, category="network", description="VPN certificate loop"),
    ]

    clusters = detect_knowledge_debt(tickets, FakeSearcher())

    assert clusters[0].ticket_ids == ["1", "2"]


def test_draft_requires_approval_and_labels_fallback() -> None:
    cluster = SimpleNamespace(
        key="network-resolved-debt",
        category="network",
        ticket_ids=["1"],
        representative_problem="VPN certificate loop",
        average_match_score=0.0,
    )

    draft = asyncio.run(draft_knowledge_article(cluster))

    assert draft.status == "pending_approval"
    assert draft.generation_mode in {"ollama", "simulated-fallback"}


def test_coverage_report_compares_before_and_after() -> None:
    report = knowledge_coverage_report([0.1, 0.4, 0.8], [0.7, 0.9, 0.8])

    assert report == {"before": 0.3333, "after": 1.0, "improvement": 0.6667}
