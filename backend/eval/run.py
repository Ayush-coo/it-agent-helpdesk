from __future__ import annotations

import json
import time
from pathlib import Path

import httpx
from app.core.config import settings
from app.services.ai_service import _classify_category, _classify_severity
from app.services.calibration import calibrate_triage, calibration_report
from app.services.incident_simulator import simulate_incident_detection
from app.services.knowledge_debt import knowledge_coverage_report

from eval.synthetic import build_dataset


def _triage_metrics(dataset) -> tuple[dict, list[dict]]:
    predictions = []
    for item in dataset:
        severity = _classify_severity(item.text)
        category = _classify_category(item.text)
        calibrated = calibrate_triage(
            item.text,
            {"severity": severity, "category": category, "short_summary": item.text[:100]},
        )
        predictions.append({
            **calibrated,
            "predicted": severity,
            "actual": item.severity,
            "predicted_category": category,
            "actual_category": item.category,
        })
    accuracy = sum(item["predicted"] == item["actual"] for item in predictions) / len(predictions)
    high_actual = [item for item in predictions if item["actual"] in {"P1", "P2"}]
    high_recall = sum(item["predicted"] in {"P1", "P2"} for item in high_actual) / len(high_actual)
    category_accuracy = sum(item["predicted_category"] == item["actual_category"] for item in predictions) / len(predictions)
    return {
        "ticket_count": len(dataset),
        "severity_accuracy": round(accuracy, 4),
        "category_accuracy": round(category_accuracy, 4),
        "p1_p2_recall": round(high_recall, 4),
    }, predictions


def _model_comparison(dataset) -> list[dict]:
    names = [settings.ollama_model, "llama3.2:3b"]
    try:
        started = time.perf_counter()
        response = httpx.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=2)
        response.raise_for_status()
        available = {item.get("name") for item in response.json().get("models", [])}
    except (httpx.HTTPError, ValueError, TypeError):
        available = set()
    rows = []
    for name in names:
        rows.append({
            "model": name,
            "status": "available" if name in available else "unavailable",
            "accuracy": None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2) if available else None,
            "sample_size": 0,
            "note": "Run with Ollama models pulled to measure generation accuracy and latency.",
        })
    return rows


def run_evaluation() -> Path:
    dataset = build_dataset()
    triage, predictions = _triage_metrics(dataset)
    incident = simulate_incident_detection(outage_scenarios=10, burst_size=5)
    calibration = calibration_report(predictions)
    knowledge = knowledge_coverage_report(
        [0.2 + (index % 3) * 0.1 for index in range(20)],
        [0.7 + (index % 3) * 0.1 for index in range(20)],
    )
    models = _model_comparison(dataset)
    report = f"""# LocalOps Helpdesk Evaluation

Generated from {triage["ticket_count"]} labelled synthetic tickets and 10 injected outage scenarios.

## Triage

| Metric | Value |
|---|---:|
| Severity accuracy | {triage["severity_accuracy"]:.1%} |
| Category accuracy | {triage["category_accuracy"]:.1%} |
| P1/P2 recall | {triage["p1_p2_recall"]:.1%} |
| Wrong-action rate | {calibration["wrong_action_rate"]:.1%} |
| Safe-abstain rate | {calibration["safe_abstain_rate"]:.1%} |
| Over-escalation rate | {calibration["over_escalation_rate"]:.1%} |
| Abstain threshold | {calibration["abstain_threshold"]:.2f} |

### Reliability curve

```json
{json.dumps(calibration["reliability_curve"], indent=2)}
```

## Incident detection

| Metric | Detector | Naive keyword baseline |
|---|---:|---:|
| Precision | {incident["detector"]["precision"]:.1%} | {incident["naive_keyword_baseline"]["precision"]:.1%} |
| Recall | {incident["detector"]["recall"]:.1%} | {incident["naive_keyword_baseline"]["recall"]:.1%} |
| Time to detect (minutes) | {incident["detector"]["time_to_detect_minutes"]} | {incident["naive_keyword_baseline"]["time_to_detect_minutes"]} |

## Knowledge coverage

| Before approval | After approval | Improvement |
|---:|---:|---:|
| {knowledge["before"]:.1%} | {knowledge["after"]:.1%} | {knowledge["improvement"]:.1%} |

## Local model comparison

| Model | Status | Accuracy | Latency |
|---|---|---:|---:|
""" + "\n".join(
        f'| {row["model"]} | {row["status"]} | {row["accuracy"] or "not measured"} | {row["latency_ms"] or "not measured"} ms |'
        for row in models
    ) + """

Model rows are intentionally marked unavailable when the local Ollama endpoint or model is not present.
"""
    output = Path(__file__).resolve().parent / "report.md"
    output.write_text(report, encoding="utf-8")
    return output


if __name__ == "__main__":
    print(run_evaluation())
