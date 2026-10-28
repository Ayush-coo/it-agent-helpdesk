from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabelledTicket:
    text: str
    severity: str
    category: str


def build_dataset() -> list[LabelledTicket]:
    templates = [
        ("VPN is unavailable for the whole clinic", "P1", "network"),
        ("Everyone cannot access the network", "P1", "network"),
        ("Possible phishing breach reported", "P1", "security"),
        ("VPN is not connecting and I cannot work", "P2", "network"),
        ("Multiple users are blocked from email", "P2", "email"),
        ("Password login is locked for one user", "P3", "access"),
        ("Printer is broken on one workstation", "P3", "hardware"),
        ("Application crashes after update", "P3", "software"),
        ("How do I install approved software?", "P4", "software"),
        ("Request a new monitor", "P4", "hardware"),
        ("How do I enroll in MFA?", "P4", "access"),
        ("Email is slow for one user", "P3", "email"),
    ]
    return [
        LabelledTicket(f"{text} (synthetic case {index})", severity, category)
        for index in range(160)
        for text, severity, category in [templates[index % len(templates)]]
    ]
