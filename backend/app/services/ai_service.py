"""Antigravity Predictive Triage & Dynamic Flow Routing Engine.

This module implements:
  1. ITIL v4 severity classification (P1-P4)
  2. Intelligent asset extraction from natural-language descriptions
  3. Dynamic agent routing based on mock system telemetry
  4. Chain-of-thought diagnostic trail generation
  5. Ollama LLM integration with robust heuristic fallback
"""
from __future__ import annotations

import json
import random
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.services.calibration import calibrate_triage


# ---------------------------------------------------------------------------
# 1.  ITIL v4 Severity Mapping  (P1 = Critical → P4 = Low)
# ---------------------------------------------------------------------------

_P1_KEYWORDS = frozenset({
    "outage", "down", "breach", "compromise", "data loss", "ransomware",
    "whole team", "everyone", "production down", "critical failure",
    "security incident", "service unavailable",
})
_P2_KEYWORDS = frozenset({
    "urgent", "immediately", "cannot work", "blocked", "major",
    "multiple users", "degraded", "significant impact",
})
_P3_KEYWORDS = frozenset({
    "cannot", "can't", "unable", "error", "failed", "failure",
    "not working", "broken", "access denied",
})
_P4_KEYWORDS = frozenset({
    "slow", "intermittent", "minor", "cosmetic", "question",
    "how to", "request", "enhancement", "would like",
})


def _classify_severity(text: str) -> str:
    """Map free-text to an ITIL P1-P4 severity level."""
    lower = text.lower()
    if any(kw in lower for kw in _P1_KEYWORDS):
        return "P1"
    if any(kw in lower for kw in _P2_KEYWORDS):
        return "P2"
    if any(kw in lower for kw in _P3_KEYWORDS):
        return "P3"
    return "P4"


def _severity_to_priority(severity: str) -> str:
    """Derive the legacy priority string from a severity level."""
    return {
        "P1": "urgent",
        "P2": "high",
        "P3": "medium",
        "P4": "low",
    }.get(severity, "medium")


# ---------------------------------------------------------------------------
# 2.  Intelligent Asset Extraction
# ---------------------------------------------------------------------------

_ASSET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("device_id", re.compile(r"\b(?:ASSET|DEV|SN|LAPTOP|PC|WS)[-_]?\d{3,10}\b", re.IGNORECASE)),
    ("ip_address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("hostname", re.compile(r"\b(?:srv|server|host|node|vm)[-_]?[a-zA-Z0-9]{2,15}\b", re.IGNORECASE)),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),
    ("application", re.compile(
        r"\b(?:Outlook|Teams|Slack|Zoom|Chrome|Firefox|Edge|Excel|Word|"
        r"PowerPoint|SAP|Salesforce|Jira|Confluence|Jenkins|GitLab|"
        r"Docker|Kubernetes|AWS|Azure|VPN|Active Directory|AD|LDAP|"
        r"SharePoint|OneDrive|Citrix|ServiceNow)\b",
        re.IGNORECASE,
    )),
    ("employee_id", re.compile(r"\b(?:EMP|USR|UID)[-_]?\d{3,8}\b", re.IGNORECASE)),
]


def _extract_assets(text: str) -> list[str]:
    """Pull structured asset identifiers out of free text."""
    found: list[str] = []
    for label, pattern in _ASSET_PATTERNS:
        for match in pattern.finditer(text):
            tag = f"{label}:{match.group(0)}"
            if tag not in found:
                found.append(tag)
    return found


# ---------------------------------------------------------------------------
# 3.  Category Classification
# ---------------------------------------------------------------------------

_CATEGORY_MAP: dict[str, list[str]] = {
    "access": ["password", "login", "access", "credentials", "signin",
               "sign-in", "vpn", "mfa", "2fa", "locked out", "account locked",
               "permission", "unauthorized", "authentication"],
    "network": ["network", "wifi", "internet", "lan", "dns", "dhcp",
                "firewall", "proxy", "connectivity", "latency", "packet loss"],
    "software": ["install", "update", "crash", "error", "bug", "app",
                 "software", "patch", "license", "deployment", "ci/cd",
                 "pipeline", "build"],
    "hardware": ["printer", "keyboard", "monitor", "hardware", "battery",
                 "laptop", "dock", "usb", "display", "screen", "mouse",
                 "headset", "webcam"],
    "email": ["email", "outlook", "mailbox", "imap", "smtp", "calendar",
              "meeting invite", "exchange"],
    "security": ["virus", "malware", "phishing", "breach", "compromise",
                 "ransomware", "suspicious", "threat", "vulnerability"],
}


def _classify_category(text: str) -> str:
    lower = text.lower()
    scores: dict[str, int] = {}
    for cat, keywords in _CATEGORY_MAP.items():
        scores[cat] = sum(1 for kw in keywords if kw in lower)
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return best if scores[best] > 0 else "general"


# ---------------------------------------------------------------------------
# 4.  Dynamic Agent Routing  (Antigravity Flow Engine)
# ---------------------------------------------------------------------------

# Mock telemetry — in production this would query a real metrics endpoint
def _get_system_telemetry() -> dict[str, Any]:
    """Simulate real-time system telemetry for dynamic routing decisions."""
    return {
        "agent_load": {
            "classifier_agent": random.uniform(0.1, 0.9),
            "troubleshooting_agent": random.uniform(0.1, 0.9),
            "knowledge_base_agent": random.uniform(0.1, 0.9),
            "access_management_agent": random.uniform(0.1, 0.9),
            "escalation_agent": random.uniform(0.1, 0.5),
        },
        "avg_resolution_time_minutes": {
            "classifier_agent": 15,
            "troubleshooting_agent": 30,
            "knowledge_base_agent": 10,
            "access_management_agent": 5,
            "escalation_agent": 60,
        },
        "system_health": "nominal",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


_CATEGORY_AGENT_MAP: dict[str, str] = {
    "access": "access_management_agent",
    "network": "troubleshooting_agent",
    "software": "knowledge_base_agent",
    "hardware": "troubleshooting_agent",
    "email": "knowledge_base_agent",
    "security": "escalation_agent",
    "general": "classifier_agent",
}

_SEVERITY_OVERRIDE: dict[str, str] = {
    "P1": "escalation_agent",
    "P2": "escalation_agent",
}


def _route_agent(severity: str, category: str) -> tuple[str, dict[str, Any]]:
    """Dynamically select the best agent based on severity, category, and
    simulated system telemetry (load balancing)."""
    telemetry = _get_system_telemetry()

    # P1/P2 always escalate regardless of category
    if severity in _SEVERITY_OVERRIDE:
        agent = _SEVERITY_OVERRIDE[severity]
        return agent, telemetry

    # Category-based primary selection
    primary = _CATEGORY_AGENT_MAP.get(category, "classifier_agent")

    # Dynamic load check — if primary agent is overloaded (>0.8), try fallback
    load = telemetry["agent_load"].get(primary, 0.5)
    if load > 0.8:
        # Find least-loaded alternative
        candidates = {
            k: v for k, v in telemetry["agent_load"].items()
            if k != "escalation_agent"
        }
        fallback = min(candidates, key=candidates.get)  # type: ignore[arg-type]
        return fallback, telemetry

    return primary, telemetry


# ---------------------------------------------------------------------------
# 5.  Summary Generation
# ---------------------------------------------------------------------------

def _short_summary(description: str) -> str:
    m = re.split(r"(?<=[.!?])\s+", description.strip())
    s = m[0] if m and m[0] else description.strip()
    return s if len(s) <= 200 else s[:197] + "..."


# ---------------------------------------------------------------------------
# 6.  Next-Steps Generation (context-aware)
# ---------------------------------------------------------------------------

def _generate_next_steps(severity: str, category: str, agent: str) -> list[str]:
    """Produce actionable next-steps tailored to the incident profile."""
    steps: list[str] = []

    # Severity-driven initial steps
    if severity == "P1":
        steps.append("IMMEDIATE: Notify on-call engineer and open bridge call")
        steps.append("Confirm scope of impact — number of affected users/systems")
    elif severity == "P2":
        steps.append("Escalate to senior engineer within 15 minutes")
        steps.append("Gather logs from affected systems")

    # Category-specific steps
    category_steps: dict[str, list[str]] = {
        "access": [
            "Verify user identity via MFA or manager confirmation",
            "Check Active Directory account status and lockout policies",
            "Execute approved credential reset workflow if identity confirmed",
        ],
        "network": [
            "Check connectivity — ping gateway, DNS resolution, VPN tunnel status",
            "Review recent network change tickets for correlated events",
            "Isolate whether issue is device-local or infrastructure-wide",
        ],
        "software": [
            "Search knowledge base for known fixes matching the error signature",
            "Check if a recent patch or deployment correlates with the issue",
            "Attempt safe remediation: clear cache, restart service, roll back update",
        ],
        "hardware": [
            "Identify device asset tag, warranty status, and last service date",
            "Run remote diagnostics if endpoint management agent is available",
            "Schedule replacement or repair through procurement if confirmed faulty",
        ],
        "email": [
            "Verify mail flow — check Exchange/SMTP queue and delivery logs",
            "Confirm mailbox quota and any active transport rules",
            "Test with Outlook Web Access to isolate client vs. server issue",
        ],
        "security": [
            "IMMEDIATE: Isolate affected endpoints from the network",
            "Preserve forensic evidence — do NOT reboot or wipe",
            "Engage Security Operations Center (SOC) for incident response",
        ],
    }
    steps.extend(category_steps.get(category, [
        "Review the request details and gather missing context",
        "Search knowledge base for similar past incidents",
        "Escalate if the request cannot be resolved at current tier",
    ]))

    return steps


# ---------------------------------------------------------------------------
# 7.  Diagnostic Trail Builder
# ---------------------------------------------------------------------------

def _build_diagnostic_trail(
    description: str,
    severity: str,
    category: str,
    agent: str,
    telemetry: dict[str, Any],
    assets: list[str],
) -> list[dict[str, Any]]:
    """Build a transparent chain-of-thought diagnostic trail."""
    now = datetime.now(timezone.utc).isoformat()
    trail: list[dict[str, Any]] = [
        {
            "step": 1,
            "action": "Intent Recognition",
            "result": f"Parsed incident description ({len(description)} chars)",
            "timestamp": now,
        },
        {
            "step": 2,
            "action": "Severity Classification",
            "result": f"Classified as {severity} via ITIL v4 keyword analysis",
            "timestamp": now,
        },
        {
            "step": 3,
            "action": "Category Classification",
            "result": f"Category: {category}",
            "timestamp": now,
        },
        {
            "step": 4,
            "action": "Asset Extraction",
            "result": f"Found {len(assets)} asset(s): {assets}" if assets else "No structured assets detected",
            "timestamp": now,
        },
        {
            "step": 5,
            "action": "Telemetry Check",
            "result": f"System health: {telemetry.get('system_health', 'unknown')}",
            "timestamp": now,
        },
        {
            "step": 6,
            "action": "Dynamic Flow Routing",
            "result": f"Routed to {agent} (load: {telemetry['agent_load'].get(agent, 'N/A'):.2f})",
            "timestamp": now,
        },
    ]

    if severity in ("P1", "P2"):
        trail.append({
            "step": 7,
            "action": "Policy Evaluation",
            "result": "HITL escalation triggered — awaiting senior engineer approval",
            "timestamp": now,
        })

    return trail


# ---------------------------------------------------------------------------
# 8.  Trigger Rules (enhanced from original)
# ---------------------------------------------------------------------------

def _apply_trigger_rules(description: str, result: dict[str, Any]) -> dict[str, Any]:
    """Apply enterprise trigger rules on top of LLM/heuristic results."""
    text = description.lower()
    normalized = dict(result)

    is_vpn = "vpn" in text
    is_password = any(term in text for term in ("password", "account locked", "reset my login"))
    is_critical = any(term in text for term in (
        "outage", "whole team", "everyone", "data loss", "breach", "compromise",
        "ransomware", "production down",
    ))

    if is_critical:
        normalized["severity"] = "P1"
        normalized["priority"] = "urgent"
        normalized["recommended_agent"] = "escalation_agent"
        normalized["requires_escalation"] = True
    elif is_vpn:
        if normalized.get("severity") not in {"P1", "P2"}:
            normalized["severity"] = "P2"
        normalized["priority"] = "high"
        normalized["recommended_agent"] = "troubleshooting_agent"
    elif is_password:
        normalized["category"] = "access"
        normalized["recommended_agent"] = "access_management_agent"

    if is_vpn:
        normalized["category"] = "network"

    if not isinstance(normalized.get("next_steps"), list) or not normalized["next_steps"]:
        normalized["next_steps"] = ["Gather the affected device, exact error, and recent changes"]

    # Ensure escalation flag for P1/P2
    if normalized.get("severity") in ("P1", "P2"):
        normalized["requires_escalation"] = True

    return normalized


# ---------------------------------------------------------------------------
# 9.  Main Entry Point — suggest_triage()
# ---------------------------------------------------------------------------

def suggest_triage(description: str) -> dict[str, Any]:
    """Perform enterprise-grade intelligent triage on an incident description.

    Tries Ollama LLM first, then falls back to the Antigravity heuristic engine.
    Returns a rich triage result with severity, category, routing, assets,
    diagnostic trail, and escalation flags.
    """

    # --- Attempt Ollama LLM inference ---
    prompt = (
        "You are the triage module of an enterprise-grade IT Operations Agent. "
        "Analyze the incoming IT incident. Return a JSON object with keys: "
        "priority (low|medium|high|urgent), "
        "severity (P1|P2|P3|P4 per ITIL v4), "
        "category (access|network|software|hardware|email|security|general), "
        "short_summary (one sentence), "
        "recommended_agent (classifier_agent|troubleshooting_agent|knowledge_base_agent|"
        "access_management_agent|escalation_agent), "
        "next_steps (list of 3-5 actionable steps), "
        "affected_assets (list of detected asset identifiers). "
        "P1 = critical business impact/outage/security breach. "
        "P2 = high impact, multiple users affected, urgent. "
        "P3 = moderate impact, single user, workaround may exist. "
        "P4 = low impact, informational, enhancement request. "
        "Respond ONLY with valid JSON.\n\n"
        f"Description: {description}\n"
    )

    try:
        url = settings.ollama_base_url.rstrip("/") + "/api/generate"
        payload = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "temperature": settings.ollama_temperature,
            "max_tokens": 512,
            "stream": False,
        }
        with httpx.Client(timeout=settings.ollama_timeout_seconds) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            text = resp.text
            try:
                data = json.loads(text)
                if isinstance(data, dict) and "response" in data:
                    inner = data["response"]
                    m = re.search(r"\{[\s\S]*\}", inner)
                    if m:
                        parsed = json.loads(m.group(0))
                        return calibrate_triage(description, _enrich_result(description, _apply_trigger_rules(description, parsed)))
                elif isinstance(data, dict):
                    return calibrate_triage(description, _enrich_result(description, _apply_trigger_rules(description, data)))
            except Exception:
                m = re.search(r"\{[\s\S]*\}", text)
                if m:
                    return calibrate_triage(description, _enrich_result(description, _apply_trigger_rules(description, json.loads(m.group(0)))))
    except Exception:
        pass

    # --- Heuristic Fallback (Antigravity Engine) ---
    severity = _classify_severity(description)
    priority = _severity_to_priority(severity)
    category = _classify_category(description)
    summary = _short_summary(description)
    assets = _extract_assets(description)
    agent, telemetry = _route_agent(severity, category)
    next_steps = _generate_next_steps(severity, category, agent)
    diagnostic_trail = _build_diagnostic_trail(
        description, severity, category, agent, telemetry, assets,
    )

    result = {
        "priority": priority,
        "severity": severity,
        "category": category,
        "short_summary": summary,
        "recommended_agent": agent,
        "next_steps": next_steps,
        "affected_assets": assets,
        "diagnostic_trail": diagnostic_trail,
        "requires_escalation": severity in ("P1", "P2"),
    }

    return calibrate_triage(description, _apply_trigger_rules(description, result))


def _enrich_result(description: str, result: dict[str, Any]) -> dict[str, Any]:
    """Ensure all enterprise fields are present even when LLM provides partial output."""
    severity = result.get("severity", _classify_severity(description))
    category = result.get("category", _classify_category(description))
    assets = result.get("affected_assets") or _extract_assets(description)
    agent = result.get("recommended_agent", _route_agent(severity, category)[0])
    _, telemetry = _route_agent(severity, category)

    result.setdefault("severity", severity)
    result.setdefault("priority", _severity_to_priority(severity))
    result.setdefault("category", category)
    result.setdefault("short_summary", _short_summary(description))
    result.setdefault("recommended_agent", agent)
    result.setdefault("next_steps", _generate_next_steps(severity, category, agent))
    result.setdefault("affected_assets", assets)
    result.setdefault("requires_escalation", severity in ("P1", "P2"))
    result["diagnostic_trail"] = _build_diagnostic_trail(
        description, severity, category, agent, telemetry, assets,
    )
    return result
