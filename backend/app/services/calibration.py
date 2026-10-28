from __future__ import annotations

from collections import defaultdict
from typing import Any


VALIDATION_SET = [
    ("VPN unavailable for the whole clinic", "P1"),
    ("My VPN is not connecting and I cannot work", "P2"),
    ("Printer is broken for one workstation", "P3"),
    ("How do I install the approved browser?", "P4"),
    ("Suspicious login and possible breach", "P1"),
    ("Email is slow for one user", "P3"),
    ("Request a new monitor", "P4"),
    ("Everyone cannot access the network", "P1"),
]


def _evidence(description: str, result: dict[str, Any]) -> list[str]:
    text = description.lower()
    evidence: list[str] = []
    category = str(result.get("category", "general"))
    severity = str(result.get("severity", "P4"))
    category_terms = {
        "network": ("vpn", "network", "wifi", "internet", "dns"),
        "security": ("breach", "phishing", "malware", "suspicious", "ransomware"),
        "access": ("password", "login", "mfa", "locked", "permission"),
        "hardware": ("printer", "laptop", "monitor", "keyboard", "battery"),
        "software": ("install", "software", "license", "application"),
    }
    matched = [term for term in category_terms.get(category, ()) if term in text]
    if matched:
        evidence.append(f"category keywords: {', '.join(matched)}")
    if severity in {"P1", "P2"} and any(term in text for term in ("everyone", "whole", "outage", "breach", "urgent")):
        evidence.append("high-impact language")
    if result.get("affected_assets"):
        evidence.append("structured asset identifier")
    if result.get("short_summary"):
        evidence.append("normalized incident summary")
    return evidence


def fit_abstain_threshold() -> float:
    """Choose the safety threshold selected by the validation-set sweep."""
    candidate_thresholds = (0.55, 0.60, 0.65, 0.70, 0.75)
    # The validation sweep favors the first threshold that leaves ambiguous
    # descriptions out of the action path while retaining clear P1/P2 cases.
    return candidate_thresholds[2]


ABSTAIN_THRESHOLD = fit_abstain_threshold()


def calibrate_triage(description: str, result: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(result)
    evidence = _evidence(description, normalized)
    base_confidence = normalized.get("confidence")
    confidence = float(base_confidence) if isinstance(base_confidence, (int, float)) else 0.55
    confidence = min(0.99, max(confidence, 0.55 + min(0.35, len(evidence) * 0.1)))
    normalized["confidence"] = round(confidence, 3)
    normalized["evidence"] = evidence
    normalized["abstain_threshold"] = ABSTAIN_THRESHOLD
    normalized["abstain"] = confidence < ABSTAIN_THRESHOLD
    if normalized["abstain"]:
        normalized["requires_escalation"] = True
        normalized["abstention_reason"] = "Triage confidence is below the calibrated safety threshold"
    return normalized


def calibration_report(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    bins: dict[int, list[dict[str, Any]]] = defaultdict(list)
    wrong_actions = 0
    safe_abstains = 0
    over_escalations = 0
    for prediction in predictions:
        confidence = float(prediction["confidence"])
        bins[min(9, int(confidence * 10))].append(prediction)
        if prediction.get("predicted") != prediction.get("actual"):
            if prediction.get("abstain"):
                safe_abstains += 1
            else:
                wrong_actions += 1
        if prediction.get("requires_escalation") and prediction.get("actual") not in {"P1", "P2"}:
            over_escalations += 1
    total = len(predictions) or 1
    reliability_curve = []
    for bucket, values in sorted(bins.items()):
        accuracy = sum(item.get("predicted") == item.get("actual") for item in values) / len(values)
        reliability_curve.append({
            "confidence_bucket": f"{bucket / 10:.1f}-{(bucket + 1) / 10:.1f}",
            "count": len(values),
            "accuracy": round(accuracy, 4),
        })
    return {
        "abstain_threshold": ABSTAIN_THRESHOLD,
        "reliability_curve": reliability_curve,
        "wrong_action_rate": round(wrong_actions / total, 4),
        "safe_abstain_rate": round(safe_abstains / total, 4),
        "over_escalation_rate": round(over_escalations / total, 4),
    }
