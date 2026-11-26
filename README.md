# LocalOps Helpdesk

[![CI](https://github.com/Ayush-coo/it-agent-helpdesk/actions/workflows/ci.yml/badge.svg)](https://github.com/Ayush-coo/it-agent-helpdesk/actions/workflows/ci.yml)

LocalOps Helpdesk is a local-first, policy-gated incident-aware IT operations agent for small teams in campuses, clinics, and MSPs where ticket text and operational evidence must stay on the network. Unlike generic employee chatbots or ticket-deflection tools, it clusters correlated failures into probable incidents, exposes evidence and calibrated uncertainty, blocks risky actions until policy and approval allow them, and keeps a tamper-evident audit trail. Ollama and Chroma provide local reasoning and retrieval; simulated adapters are clearly marked until connected to real systems.

## Architecture

```mermaid
flowchart LR
    UI[React employee and agent console] --> API[FastAPI API]
    API --> AUTH[JWT and RBAC]
    API --> CHAT[LangGraph chat workflow]
    CHAT --> CONVERSATIONS[(Conversations and messages)]
    CHAT --> AGENTTOOLS[Role-checked agent tools]
    API --> TICKETS[(PostgreSQL tickets)]
    API --> INCIDENTS[(Probable incidents)]
    API --> POLICY[YAML policy engine]
    POLICY --> RUNBOOKS[Simulated runbook adapters]
    API --> AUDIT[(Hash-chained audit log)]
    API --> RAG[Chroma retrieval]
    RAG --> OLLAMA[Local Ollama]
    API --> EVAL[Replayable evaluation]
    API --> SLACK[Slack adapter or mock fallback]
```

## Feature status

| Capability | Status | Notes |
|---|---|---|
| Stateful helpdesk agent | Real / simulated identity adapter | LangGraph, last-10-message context, citations, ticket handoff, and next-turn OTP confirmation |
| JWT auth, RBAC, ticket lifecycle | Real | Persisted through SQLAlchemy/Alembic |
| Probable-incident clustering | Real | Time window, shared attributes, Ollama embeddings with lexical fallback |
| Outage replay simulator | Real | Deterministic synthetic traffic and naive baseline comparison |
| YAML runbook policy | Real | Risk, approver, preconditions, dry-run, rollback, rate/hours metadata |
| Runbook infrastructure changes | Simulated | Handlers return simulated outcomes; no endpoint or IAM mutation occurs |
| Calibrated abstention | Real | Evidence, threshold, reliability curve, safety metrics |
| Knowledge-debt drafting | Real / simulated fallback | Human approval is required before Chroma ingestion |
| Ollama reasoning and Chroma retrieval | Real when local services are available | No cloud model dependency |
| Slack notification | Real adapter / mock fallback | Configure `SLACK_WEBHOOK_URL` to use the webhook |
| Recruitment page | Legacy and unrelated | Retained by request; not part of the LocalOps thesis |

## Quickstart

### Docker

```powershell
Copy-Item .env.example .env
# Set JWT_SECRET_KEY to a long random value before using production mode.
docker compose up --build
```

Open `http://localhost:5173/login`. The backend API is at `http://localhost:8000/docs`; metrics are at `http://localhost:8000/metrics`. Docker starts PostgreSQL, Ollama, Chroma persistence, Alembic migrations, and the nginx-served frontend. Pull local models separately when Ollama is ready:

```powershell
docker exec it-agent-ollama ollama pull llama3.1:8b
docker exec it-agent-ollama ollama pull nomic-embed-text
```

### Host development

```powershell
Copy-Item .env.example .env
.\start-dev.ps1
```

Or run the backend from `backend/` and the frontend from `frontend/` separately. Host development defaults to PostgreSQL on `localhost`; Compose overrides the database hostname to `db`.

## Validation and evaluation

```powershell
cd backend
python -m pytest tests
python -m eval.run
python -m scripts.verify_audit
```

The evaluation command writes [`backend/eval/report.md`](backend/eval/report.md) from 160 labelled synthetic tickets and 10 outage scenarios. The current measured results are:

| Metric | Result |
|---|---:|
| Severity accuracy | 66.9% |
| Category accuracy | 73.8% |
| P1/P2 recall | 79.7% |
| Incident precision / recall | 100.0% / 100.0% |
| Incident time to detect | 1.9 minutes |
| Knowledge coverage before / after | 0.0% / 100.0% |

Local model latency/accuracy is reported as unavailable when Ollama models are not present; no unmeasured model claim is included.

## Security model

- Production startup rejects the default JWT secret.
- PII and secrets are redacted before text reaches the local LLM.
- Ticket text cannot approve or bypass policy decisions.
- User and knowledge-base text cannot grant tool permissions or authorize access to other users' data.
- Password reset and account unlock require a mock OTP and explicit confirmation in a later chat turn; results are recorded in ticket events.
- Dry-run is the default for every policy action.
- State-changing actions require the configured approver role and explicit approval.
- Every action decision and outcome is recorded in a hash chain that can be verified.
- P1/P2 and low-confidence triage abstain or escalate instead of guessing.
- Simulated adapters never claim to have changed external infrastructure.

## Limitations

- Runbooks are simulated and require real adapters for IAM, endpoint, VPN, and print systems.
- Ollama model quality depends on the locally installed model and hardware.
- The lexical embedding fallback is less precise than a live Ollama embedding model.
- The evaluation data is synthetic and should not be presented as production accuracy.
- Docker, Ollama model pulls, and Slack delivery were not verifiable in this Windows environment because Docker was unavailable.
- Recruitment remains as an isolated legacy demo because deletion was not approved.

## Roadmap

1. Connect approved IAM, endpoint, network, and ITSM adapters behind the existing policy interface.
2. Add production-labelled incident and KB datasets with human-reviewed calibration.
3. Add SSO, asset inventory, SLA reporting, and notification delivery.
4. Remove or archive the legacy recruitment demo after explicit approval.

## Resume bullets

- Built a local-first incident-aware IT operations agent with 100% incident precision and 100% recall across 10 injected outage scenarios.
- Implemented evidence-based triage achieving 66.9% severity accuracy, 73.8% category accuracy, and 79.7% P1/P2 recall on 160 labelled synthetic tickets.
- Added calibrated abstention, policy-gated simulated runbooks, PII redaction, and tamper-evident audit verification for safe local operations.
- Added a knowledge-debt loop that increased synthetic retrieval coverage from 0.0% to 100.0% after approved article ingestion.
