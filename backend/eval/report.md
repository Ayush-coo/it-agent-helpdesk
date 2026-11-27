# LocalOps Helpdesk Evaluation

Generated from 138 unique labelled synthetic tickets.

## Triage

| Metric | Value |
|---|---:|
| Severity accuracy | 67.4% |
| Category accuracy | 76.1% |
| P1/P2 recall | 68.5% |
| Wrong-action rate | 25.4% |
| Safe-abstain rate | 7.2% |
| Over-escalation rate | 23.2% |
| Abstain threshold | 0.70 |

### Reliability curve

```json
[
  {
    "confidence_bucket": "0.7-0.8",
    "count": 138,
    "accuracy": 0.6739
  }
]
```

## Held-out retrieval

Hit rate@3 on 8 held-out questions: **62.5%**

The retrieval score is computed by querying a fixed local article corpus with held-out
questions and checking whether the labelled relevant article appears in the top three.
