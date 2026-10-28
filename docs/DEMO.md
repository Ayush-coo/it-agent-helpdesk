# LocalOps Helpdesk — 90-second demo

This script demonstrates the local-first incident and policy controls. The runbook adapter is simulated; the policy decision and audit chain are real.

## 0:00–0:15 — Start locally

```powershell
docker compose up --build
```

Open `http://localhost:5173/login`, enter the demo workspace, and open the agent dashboard.

## 0:15–0:35 — Inject an outage burst

Create three tickets in the API or UI with the same service, site, and outage signature:

```text
VPN service unavailable for multiple users at north campus; subnet 10.1.0.0/16
```

After the threshold is crossed, open `GET /api/v1/incidents` as an agent. Show the probable incident, linked ticket IDs, timeline, root-cause hypothesis, and suggested owner. New matching tickets link to the same incident instead of creating duplicate escalations.

## 0:35–0:55 — Show calibrated triage

Submit an ambiguous request and a high-impact outage. Show the returned priority, category, confidence, evidence, and abstention threshold. The ambiguous request escalates rather than inventing a fix.

## 0:55–1:15 — Block then approve a risky action

Request a non-dry-run endpoint service restart without approval:

```json
{
  "runbook_name": "restart_endpoint_service",
  "params": {"device_id": "DEV-100", "service_name": "agent"},
  "dry_run": false,
  "approved": false
}
```

The policy engine returns `needs_approval`. Repeat with an approved admin token; the simulated adapter runs and records the policy decision, risk tier, blast radius, and rollback steps.

## 1:15–1:30 — Verify the audit chain

```powershell
cd backend
python -m scripts.verify_audit
```

Show `"valid": true`, then open `/metrics` to show request counters. The point of the demo is not autonomous remediation; it is controlled, explainable local operations.
