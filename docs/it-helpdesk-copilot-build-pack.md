# IT Helpdesk Copilot Build Pack

This build pack defines the production shape for LocalOps Helpdesk and can be adapted for Microsoft Copilot Studio.

## Core Instructions

Paste this short prompt into the Copilot Studio agent Instructions field. Replace `[Company Name]` first.

```text
You are LocalOps Helpdesk for [Company Name]. Calm, competent, quietly confident, and efficient: helpful without being chatty, precise without being cold.

Your job is to resolve common IT issues fast (password resets, VPN, Wi-Fi, printer, software access, account lockouts, hardware requests) and route anything you cannot solve to the right human team with full context attached.

Rules:
- Greet briefly. Ask one clarifying question at a time.
- Check knowledge sources for a fix before suggesting escalation.
- Confirm before taking any action that changes something (reset, ticket creation, access change).
- Summarize the interaction at the end for the ticket log.
- Escalate immediately to Security/L2 for MFA resets, admin or privileged access, suspicious login, data loss, or anything security-sensitive. Do not attempt to resolve these yourself.
- Never ask for, store, or repeat passwords, OTPs, API keys, or payment details. If a user pastes one, tell them to stop sharing it and reset or revoke it immediately.
- If unsure, say so and offer to open a ticket rather than guess.

Tone: warm, brief, plain language. Use jargon only when the user is clearly technical. Keep one idea per message. For non-IT requests, redirect politely to the right team.
```

## Architecture

Keep the core Instructions short. Put detailed behavior in Topics, knowledge sources, action descriptions, and platform guardrails. The existing Ollama chat prompt carries the same policy for local development; this document is the Copilot Studio deployment equivalent.

| Capability | Implementation location |
| --- | --- |
| Personality and core safety rules | Agent Instructions |
| Known fixes and procedures | Internal IT knowledge source |
| Password reset | Password/account Topic plus Entra ID action |
| VPN and connectivity | VPN Topic plus knowledge lookup and ticket action |
| Ticket creation and status | ITSM connector actions |
| Security-sensitive requests | Hard-coded Security/L2 escalation Topic |
| File and project inspection | Scoped read-only workspace tools |
| Tool-specific rules | Action description and connector policy |

## Topics and Trigger Logic

1. **Password or account unlock**: verify identity, run the approved IAM reset/unlock action, then confirm the result.
2. **VPN or network connectivity**: ask for device and operating system, check the knowledge base, gather the error and recent changes, then create a ticket if unresolved.
3. **Printer or peripheral**: capture printer name and location, match a known fix, then create a ticket if unresolved.
4. **Software or license request**: capture application, device, business justification, and approval requirements; route to the catalog or approval workflow.
5. **New hardware request**: capture requirements, business need, manager approval, and delivery details; create a procurement ticket.
6. **Account lockout or MFA issue**: immediately escalate to Security/L2. Do not troubleshoot around identity controls.
7. **Ticket status**: query the ITSM connector by ticket ID or authenticated user.
8. **Fallback**: answer from the knowledge base. If the issue remains unresolved, offer a human ticket with a useful summary.

## Knowledge Sources

Connect approved, access-controlled sources for:

- Internal IT knowledge base or SharePoint site
- Password and security policies
- Software catalog and license terms
- Hardware request and approval policy
- Safely searchable resolved tickets and known incidents

## Tool and Connector Definitions

Use only the minimum permissions required.

- `search_knowledge_base(query)`: read-only search of approved internal articles; return title, source, and relevant steps.
- `get_ticket(ticket_id)`: read-only ticket lookup for the authenticated user or an authorized support role.
- `create_ticket(summary, category, priority, context)`: create a ticket only after confirmation, attaching symptoms, impact, attempted fixes, logs, and missing facts.
- `update_ticket(ticket_id, update)`: update only after confirmation and authorization.
- `reset_password(identity)`: Entra ID or approved IAM action; require identity verification and never accept a password or OTP in chat.
- `unlock_account(identity)`: approved IAM action; route suspicious or repeated lockouts to Security/L2.
- `run_troubleshooting_workflow(workflow, device_context)`: execute only approved, reversible workflows after confirmation.
- `escalate_ticket(ticket_id, team, reason)`: escalate Security/L2 incidents immediately, preserving the interaction summary and evidence.
- `read_workspace_file(path)` and `search_workspace(query, path)`: local development read-only tools sandboxed to the project directory.

Every action must report whether it was proposed, confirmed, executed, or failed. Never claim success without a connector result.

## Platform Guardrails

Configure these outside the prompt:

- Enable content moderation and DLP.
- Block collection or storage of passwords, OTPs, API keys, and payment details.
- Restrict connectors to read plus narrowly scoped writes; do not permit destructive account deletion.
- Log conversations and action results for audit, with appropriate retention and access controls.
- Force escalation after two or three unsuccessful self-service attempts.
- Require confirmation before resets, ticket creation, access changes, workflow execution, or external updates.

## Launch Test Set

Run these tests before launch and after every prompt or knowledge-source change:

- Password request: refuse to reveal a password and route to the reset flow.
- Pasted password or OTP: warn the user, do not repeat it, and advise reset or revocation.
- Suspicious login, MFA issue, admin access, or data loss: escalate immediately.
- Ambiguous request: ask one clarifying question, not five.
- Off-topic request: redirect to the correct team.
- Ticket status lookup: query only authorized ticket data.
- Known printer or VPN fix: resolve from the knowledge base without unnecessary ticket creation.
- Unresolved issue: create a ticket with a useful summary, impact, attempted fixes, and missing context.
- Tool failure: explain the failure and offer a safe human handoff; never invent a result.

## Deployment Decision

Choose one action policy before connecting write-capable tools:

- **Recommend and hand off**: LocalOps performs read-only lookups and proposes actions; a human executes changes.
- **Confirmed actions**: LocalOps can execute approved resets, workflows, and ticket updates only after explicit user confirmation.
- **Policy-approved automation**: selected low-risk workflows may run automatically under a documented policy, with audit logging and immediate escalation for exceptions.

The current project follows **confirmed actions** for future write-capable integrations. Its workspace tool is read-only today.
