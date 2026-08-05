from __future__ import annotations

import json
from typing import List

from app.services.ai_service import suggest_triage


def demo(descriptions: List[str]) -> None:
    for i, desc in enumerate(descriptions, 1):
        print(f"--- Example {i} ---")
        print("Description:", desc)
        result = suggest_triage(desc)
        print(json.dumps(result, indent=2))
        print()


if __name__ == "__main__":
    samples = [
        "My VPN is not connecting and I need access immediately",
        "Email sync is failing with an error after the latest update",
        "Request to install Slack for a new hire",
        "Printer is jammed and not responding",
    ]
    demo(samples)
