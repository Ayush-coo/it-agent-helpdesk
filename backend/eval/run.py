from __future__ import annotations

import json
from pathlib import Path

from app.services.ai_service import _classify_category, _classify_severity
from app.services.calibration import calibrate_triage, calibration_report

from eval.retrieval import retrieval_hit_rate
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


def run_evaluation() -> Path:
    dataset = build_dataset()
    triage, predictions = _triage_metrics(dataset)
    calibration = calibration_report(predictions)
    retrieval = retrieval_hit_rate()
    report = f"""# LocalOps Helpdesk Evaluation

Generated from {triage["ticket_count"]} unique labelled synthetic tickets.

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

## Held-out retrieval

Hit rate@3 on {retrieval["question_count"]} held-out questions: **{retrieval["hit_rate_at_3"]:.1%}**

The retrieval score is computed by querying a fixed local article corpus with held-out
questions and checking whether the labelled relevant article appears in the top three.
"""
    output = Path(__file__).resolve().parent / "report.md"
    output.write_text(report, encoding="utf-8")
    return output


if __name__ == "__main__":
    print(run_evaluation())
