from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass(frozen=True)
class SimulatedTicket:
    ticket_id: str
    created_at: datetime
    description: str
    service: str
    site: str
    incident_id: str | None = None


def _scores(predictions: set[str], actual: set[str], delays: list[float]) -> dict[str, Any]:
    true_positive = len(predictions & actual)
    precision = true_positive / len(predictions) if predictions else 0.0
    recall = true_positive / len(actual) if actual else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "time_to_detect_minutes": round(sum(delays) / len(delays), 2) if delays else None,
        "detected": true_positive,
        "predicted": len(predictions),
        "actual": len(actual),
    }


def simulate_incident_detection(
    *,
    seed: int = 7,
    normal_tickets: int = 100,
    outage_scenarios: int = 10,
    burst_size: int = 5,
    threshold: int = 3,
) -> dict[str, Any]:
    """Replay normal traffic and injected bursts against the incident detector."""
    rng = random.Random(seed)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    services = ["vpn", "email", "wifi", "printing", "ehr"]
    sites = ["north", "south", "clinic-a"]
    tickets: list[SimulatedTicket] = []
    actual: set[str] = set()

    for index in range(normal_tickets):
        service = rng.choice(services)
        tickets.append(
            SimulatedTicket(
                ticket_id=f"normal-{index}",
                created_at=start + timedelta(minutes=index * 3),
                description=f"{service} intermittent issue on one workstation",
                service=service,
                site=rng.choice(sites),
            )
        )

    cursor = start + timedelta(minutes=normal_tickets * 3 + 10)
    for scenario in range(outage_scenarios):
        incident_id = f"incident-{scenario}"
        actual.add(incident_id)
        service = services[scenario % len(services)]
        site = sites[scenario % len(sites)]
        for member in range(burst_size):
            tickets.append(
                SimulatedTicket(
                    ticket_id=f"{incident_id}-ticket-{member}",
                    created_at=cursor + timedelta(minutes=member),
                    description=f"{service} service unavailable for multiple users",
                    service=service,
                    site=site,
                    incident_id=incident_id,
                )
            )
        cursor += timedelta(minutes=45)

    predictions: set[str] = set()
    delays: list[float] = []
    for ticket in tickets:
        recent = [
            item for item in tickets
            if item.created_at <= ticket.created_at
            and ticket.created_at - item.created_at <= timedelta(minutes=30)
            and item.service == ticket.service
            and item.site == ticket.site
        ]
        if len(recent) >= threshold and ticket.incident_id:
            if ticket.incident_id not in predictions:
                predictions.add(ticket.incident_id)
                first = next(item for item in recent if item.incident_id == ticket.incident_id)
                delays.append((ticket.created_at - first.created_at).total_seconds() / 60)

    return {
        "seed": seed,
        "ticket_count": len(tickets),
        "outage_scenarios": outage_scenarios,
        "detector": _scores(predictions, actual, delays),
    }
