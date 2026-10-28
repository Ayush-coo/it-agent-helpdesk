from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.core.config import settings
from app.models.ticket import TicketStatus


class KnowledgeSearcher(Protocol):
    def search(self, query: str, limit: int) -> list[Any]: ...


@dataclass(frozen=True)
class KnowledgeDebtCluster:
    key: str
    category: str
    ticket_ids: list[str]
    representative_problem: str
    average_match_score: float


@dataclass(frozen=True)
class KnowledgeDraft:
    cluster_key: str
    title: str
    content: str
    source: str
    status: str
    generation_mode: str


def detect_knowledge_debt(
    tickets: list[Any],
    searcher: KnowledgeSearcher,
    *,
    match_threshold: float = 0.55,
) -> list[KnowledgeDebtCluster]:
    groups: dict[str, list[Any]] = defaultdict(list)
    for ticket in tickets:
        if ticket.status != TicketStatus.RESOLVED:
            continue
        category = (ticket.category or "general").strip().lower()
        hits = searcher.search(ticket.description, 1)
        score = float(hits[0].score) if hits else 0.0
        if score < match_threshold:
            groups[category].append((ticket, score))

    clusters = []
    for category, members in groups.items():
        clusters.append(
            KnowledgeDebtCluster(
                key=f"{category}-resolved-debt",
                category=category,
                ticket_ids=[ticket.id for ticket, _ in members],
                representative_problem=members[0][0].description,
                average_match_score=round(sum(score for _, score in members) / len(members), 4),
            )
        )
    return clusters


async def _ollama_draft(cluster: KnowledgeDebtCluster) -> str | None:
    prompt = (
        "Draft a concise internal IT knowledge article from this resolved-ticket pattern. "
        "Do not invent commands, credentials, or destructive steps. Return JSON with "
        "title and content only.\n"
        f"Category: {cluster.category}\nProblem: {cluster.representative_problem}\n"
    )
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            payload = response.json()
            raw = payload.get("response", "")
            data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
            return f"{data['title']}\n\n{data['content']}"
    except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError):
        return None


async def draft_knowledge_article(cluster: KnowledgeDebtCluster) -> KnowledgeDraft:
    generated = await _ollama_draft(cluster)
    if generated:
        title, _, content = generated.partition("\n\n")
        mode = "ollama"
    else:
        title = f"Troubleshooting {cluster.category} incidents"
        content = (
            f"Observed pattern: {cluster.representative_problem}\n\n"
            "Resolution steps must be verified by an IT agent before publication.\n"
            "Escalate when the issue affects multiple sites, security controls, or data integrity."
        )
        mode = "simulated-fallback"
    return KnowledgeDraft(cluster.key, title, content, "knowledge-debt-loop", "pending_approval", mode)


def knowledge_coverage_report(before_scores: list[float], after_scores: list[float]) -> dict[str, float]:
    def coverage(scores: list[float]) -> float:
        return round(sum(score >= 0.55 for score in scores) / len(scores), 4) if scores else 0.0

    before = coverage(before_scores)
    after = coverage(after_scores)
    return {"before": before, "after": after, "improvement": round(after - before, 4)}
