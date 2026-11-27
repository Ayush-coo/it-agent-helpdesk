from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


VALIDATION_SET = [
    ("VPN unavailable for the whole clinic", "P1", "P1", 0.90),
    ("My VPN is not connecting and I cannot work", "P2", "P2", 0.85),
    ("Printer is broken for one workstation", "P3", "P3", 0.70),
    ("How do I install the approved browser?", "P4", "P4", 0.70),
    ("Suspicious login and possible breach", "P1", "P1", 0.90),
    ("Email is slow for one user", "P3", "P3", 0.70),
    ("Request a new monitor", "P4", "P4", 0.70),
    ("Unclear problem", "P4", "P3", 0.55),
]


def fit_abstain_threshold() -> float:
    """Choose the lowest confidence cutoff that is fully correct on validation labels."""
    candidates = sorted({score for _, _, _, score in VALIDATION_SET})
    for threshold in candidates:
        accepted = [item for item in VALIDATION_SET if item[3] >= threshold]
        if accepted and all(predicted == actual for _, actual, predicted, _ in accepted):
            return threshold
    return max(candidates)


ABSTAIN_THRESHOLD = fit_abstain_threshold()

_KEYWORD_PATTERN = re.compile(
    r"\b(?:outage|down|breach|compromis\w*|data loss|ransomware|phishing|"
    r"suspicious|malware|virus|password|login|access|vpn|mfa|locked|permission|"
    r"network|wi-?fi|internet|lan|dns|dhcp|firewall|proxy|connectivity|"
    r"printer|keyboard|monitor|hardware|battery|laptop|software|install|"
    r"update|crash\w*|error|bug|email|outlook|mailbox|exchange)\b",
    re.IGNORECASE,
)


def calibrate_triage(
    description: str,
    result: dict[str, Any],
    *,
    rules_disagree: bool = False,
) -> dict[str, Any]:
    normalized = dict(result)
    evidence = [match.group(0) for match in _KEYWORD_PATTERN.finditer(description)]
    confidence_value = normalized.get("confidence")
    confidence = (
        float(confidence_value)
        if isinstance(confidence_value, (int, float))
        else 0.70
    )
    normalized["confidence"] = round(min(0.99, max(0.0, confidence)), 3)
    normalized["evidence"] = list(dict.fromkeys(evidence))
    normalized["abstain_threshold"] = ABSTAIN_THRESHOLD
    reasons = []
    if normalized.get("category") == "general":
        reasons.append("Triage category is general")
    if not evidence:
        reasons.append("No keyword evidence was found")
    if rules_disagree:
        reasons.append("LLM triage disagrees with deterministic rules")
    if confidence < ABSTAIN_THRESHOLD:
        reasons.append("Triage confidence is below the calibrated safety threshold")
    normalized["abstain"] = bool(reasons)
    normalized["rules_disagree"] = rules_disagree
    if reasons:
        normalized["requires_escalation"] = True
        normalized["abstention_reason"] = "; ".join(reasons)
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
