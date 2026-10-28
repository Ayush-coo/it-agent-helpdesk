# LocalOps Helpdesk Evaluation

Generated from 160 labelled synthetic tickets and 10 injected outage scenarios.

## Triage

| Metric | Value |
|---|---:|
| Severity accuracy | 66.9% |
| Category accuracy | 73.8% |
| P1/P2 recall | 79.7% |
| Wrong-action rate | 33.1% |
| Safe-abstain rate | 0.0% |
| Over-escalation rate | 0.0% |
| Abstain threshold | 0.65 |

### Reliability curve

```json
[
  {
    "confidence_bucket": "0.6-0.7",
    "count": 54,
    "accuracy": 0.5
  },
  {
    "confidence_bucket": "0.7-0.8",
    "count": 92,
    "accuracy": 0.7174
  },
  {
    "confidence_bucket": "0.8-0.9",
    "count": 14,
    "accuracy": 1.0
  }
]
```

## Incident detection

| Metric | Detector | Naive keyword baseline |
|---|---:|---:|
| Precision | 100.0% | 100.0% |
| Recall | 100.0% | 100.0% |
| Time to detect (minutes) | 1.9 | 2.0 |

## Knowledge coverage

| Before approval | After approval | Improvement |
|---:|---:|---:|
| 0.0% | 100.0% | 100.0% |

## Local model comparison

| Model | Status | Accuracy | Latency |
|---|---|---:|---:|
| llama3.1:8b | unavailable | not measured | not measured ms |
| llama3.2:3b | unavailable | not measured | not measured ms |

Model rows are intentionally marked unavailable when the local Ollama endpoint or model is not present.
