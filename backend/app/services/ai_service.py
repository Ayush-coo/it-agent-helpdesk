from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import settings


def _heuristic_priority(description: str) -> str:
    text = description.lower()
    if any(k in text for k in ("down", "outage", "urgent", "immediately", "failure")):
        return "urgent"
    if any(k in text for k in ("cannot", "can't", "unable", "error", "failed", "failure")):
        return "high"
    if any(k in text for k in ("slow", "intermittent", "issue", "problem")):
        return "medium"
    return "low"


def _heuristic_category(description: str) -> str:
    text = description.lower()
    mapping = {
        "access": ["password", "login", "access", "credentials", "signin", "sign-in", "vpn"],
        "network": ["network", "wifi", "internet", "lan"],
        "software": ["install", "update", "crash", "error", "bug", "app", "software"],
        "hardware": ["printer", "keyboard", "monitor", "hardware", "battery", "laptop"],
        "email": ["email", "outlook", "mailbox", "imap", "smtp"],
    }
    for cat, keys in mapping.items():
        if any(k in text for k in keys):
            return cat
    return "general"


def _short_summary(description: str) -> str:
    # Take first sentence or first 120 chars
    m = re.split(r"(?<=[.!?])\s+", description.strip())
    if m and m[0]:
        s = m[0]
    else:
        s = description.strip()
    return s if len(s) <= 200 else s[:197] + "..."


def suggest_triage(description: str) -> dict[str, Any]:
    """Try to use local Ollama to suggest priority/category/summary plus agent routing.

    Falls back to lightweight heuristics if Ollama is unavailable.
    """
    prompt = (
        "You are an assistant that reads an IT support ticket description and returns a JSON object with keys:"
        " priority, category, short_summary, recommended_agent, and next_steps."
        " Priority must be one of: low, medium, high, urgent."
        " Category should be a single word like network, access, software, hardware, email, or general."
        " recommended_agent should be one of: classifier_agent, troubleshooting_agent, knowledge_base_agent, access_management_agent, escalation_agent."
        " next_steps should be a short list of actionable steps."
        " Respond ONLY with valid JSON.\n\n"
        f"Description: {description}\n"
    )

    # Try Ollama local inference
    try:
        url = settings.ollama_base_url.rstrip("/") + "/api/generate"
        payload = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "temperature": settings.ollama_temperature,
            "max_tokens": 256,
        }
        with httpx.Client(timeout=settings.ollama_timeout_seconds) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            text = resp.text
            # Try to extract JSON from the response body
            try:
                data = json.loads(text)
                # If model returns nested structure, try to find the first JSON-like string
                if isinstance(data, dict) and ("content" in data or "choices" in data):
                    # attempt to locate JSON inside strings
                    body = json.dumps(data)
                    idx = body.find("{")
                    if idx != -1:
                        body = body[idx:]
                        return json.loads(body)
                else:
                    return data
            except Exception:
                # fallback: find first JSON object in text
                m = re.search(r"\{[\s\S]*\}", text)
                if m:
                    return json.loads(m.group(0))
    except Exception:
        # Ollama unavailable or failed; fall through to heuristics
        pass

    # Heuristic fallback
    priority = _heuristic_priority(description)
    category = _heuristic_category(description)
    summary = _short_summary(description)

    if category == "access":
        recommended_agent = "access_management_agent"
        next_steps = ["Verify account access and credentials", "Check authentication policies", "Escalate if the issue persists"]
    elif category == "network":
        recommended_agent = "troubleshooting_agent"
        next_steps = ["Check connectivity and VPN status", "Review recent network incidents", "Escalate to infrastructure support if needed"]
    elif category == "software":
        recommended_agent = "knowledge_base_agent"
        next_steps = ["Search the knowledge base for known fixes", "Check recent software changes", "Escalate if setup is still failing"]
    else:
        recommended_agent = "classifier_agent"
        next_steps = ["Review the request details", "Gather any missing context", "Escalate if the request is urgent"]

    return {
        "priority": priority,
        "category": category,
        "short_summary": summary,
        "recommended_agent": recommended_agent,
        "next_steps": next_steps,
    }
