from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.incident import Incident, IncidentStatus, IncidentTicket
from app.models.ticket import EscalationStatus, Ticket


_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]{2,}", re.IGNORECASE)


@dataclass(frozen=True)
class IncidentDetectionResult:
    incident: Incident | None
    linked_ticket_ids: list[str]
    similarity_mode: str
    duplicate_escalation_suppressed: bool


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


def lexical_embedding(text: str, dimensions: int = 128) -> list[float]:
    """Deterministic local fallback used when the Ollama embedding endpoint is unavailable."""
    vector = [0.0] * dimensions
    for token in _tokens(text):
        vector[hash(token) % dimensions] += 1.0
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


async def ollama_embedding(text: str) -> list[float] | None:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/embeddings",
                json={"model": settings.ollama_embedding_model, "prompt": text},
            )
            response.raise_for_status()
            embedding = response.json().get("embedding")
            return embedding if isinstance(embedding, list) and embedding else None
    except (httpx.HTTPError, ValueError, TypeError):
        return None


def _shared_attributes(left: Ticket, right: Ticket) -> set[str]:
    attributes = {"service", "site", "subnet", "asset_group"}
    return {
        attribute
        for attribute in attributes
        if getattr(left, attribute, None)
        and getattr(left, attribute, None) == getattr(right, attribute, None)
    }


def _ticket_text(ticket: Ticket) -> str:
    return " ".join(
        value for value in (
            ticket.title,
            ticket.description,
            ticket.category,
            ticket.service,
            ticket.site,
            ticket.subnet,
            ticket.asset_group,
        )
        if value
    )


def _hypothesis(tickets: list[Ticket]) -> str:
    words = Counter(
        token
        for ticket in tickets
        for token in _tokens(_ticket_text(ticket))
        if token not in {"the", "and", "for", "with", "from", "this", "that"}
    )
    common = [word for word, count in words.most_common(4) if count >= 2]
    return (
        f"Shared failure signature across {len(tickets)} tickets: {', '.join(common)}."
        if common
        else "Common service or asset attributes indicate a correlated failure."
    )


def _owner(tickets: list[Ticket]) -> str:
    category = next((ticket.category for ticket in tickets if ticket.category), "general")
    return {
        "network": "network_operations",
        "access": "identity_and_access",
        "software": "application_support",
        "hardware": "endpoint_support",
        "security": "security_operations",
    }.get(category, "service_desk")


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


async def detect_and_link(
    session: AsyncSession,
    ticket: Ticket,
) -> IncidentDetectionResult:
    cutoff = _as_utc(ticket.created_at or datetime.now(timezone.utc)) - timedelta(
        minutes=settings.incident_window_minutes
    )
    result = await session.execute(
        select(Ticket).where(Ticket.id != ticket.id, Ticket.created_at >= cutoff)
    )
    candidates = list(result.scalars().all())
    current_embedding = await ollama_embedding(_ticket_text(ticket))
    mode = "ollama"
    if current_embedding is None:
        current_embedding = lexical_embedding(_ticket_text(ticket))
        mode = "lexical-fallback"

    matches: list[tuple[Ticket, float, set[str]]] = []
    for candidate in candidates:
        candidate_embedding = await ollama_embedding(_ticket_text(candidate)) if mode == "ollama" else None
        if candidate_embedding is None:
            candidate_embedding = lexical_embedding(_ticket_text(candidate))
            if mode == "ollama":
                mode = "mixed"
        similarity = cosine_similarity(current_embedding, candidate_embedding)
        shared = _shared_attributes(ticket, candidate)
        if similarity >= settings.incident_similarity_threshold and shared:
            matches.append((candidate, similarity, shared))

    if not matches:
        return IncidentDetectionResult(None, [], mode, False)

    related = [ticket] + [match[0] for match in matches]
    existing_id = next((item.incident_id for item in related if item.incident_id), None)
    incident = None
    suppressed = False

    if existing_id:
        incident = await session.get(Incident, existing_id)
    elif len(related) >= settings.incident_min_members:
        common = next((match[2] for match in matches if match[2]), set())
        incident = Incident(
            title=f"Probable incident: {ticket.title[:160]}",
            status=IncidentStatus.PROBABLE,
            service=ticket.service,
            site=ticket.site,
            subnet=ticket.subnet,
            asset_group=ticket.asset_group,
            member_count=0,
            first_seen_at=min(_as_utc(item.created_at) for item in related),
            last_seen_at=max(_as_utc(item.created_at) for item in related),
            root_cause_hypothesis=_hypothesis(related),
            suggested_owner=_owner(related),
            timeline=[],
        )
        session.add(incident)
        await session.flush()

    if incident is None:
        return IncidentDetectionResult(None, [], mode, False)

    timeline = list(incident.timeline or [])
    for member in related:
        member.incident_id = incident.id
        if member.id != ticket.id and member.escalation_status == EscalationStatus.PENDING_REVIEW:
            member.escalation_status = EscalationStatus.NONE
            member.incident_escalation_suppressed = True
            suppressed = True
        association = await session.get(
            IncidentTicket, {"incident_id": incident.id, "ticket_id": member.id}
        )
        if association is None:
            similarity = next(
                (value for candidate, value, _ in matches if candidate.id == member.id),
                1.0,
            )
            session.add(
                IncidentTicket(
                    incident_id=incident.id,
                    ticket_id=member.id,
                    similarity=similarity,
                )
            )
            timeline.append({
                "ticket_id": member.id,
                "timestamp": _as_utc(member.created_at).isoformat(),
                "similarity": round(similarity, 4),
            })

    incident.member_count = len(timeline)
    incident.last_seen_at = max(_as_utc(item.created_at) for item in related)
    incident.timeline = timeline
    incident.root_cause_hypothesis = _hypothesis(related)
    return IncidentDetectionResult(
        incident,
        [member.id for member in related],
        mode,
        suppressed,
    )
