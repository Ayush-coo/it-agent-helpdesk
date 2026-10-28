from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from app.models.user import UserRole


@dataclass(frozen=True)
class PolicyDecision:
    decision: str
    reason: str
    risk_tier: str
    blast_radius: str
    rollback_steps: list[str]
    dry_run: bool
    can_execute: bool


def _policy_path() -> Path:
    return Path(__file__).resolve().parents[2] / "policies" / "runbooks.yaml"


def load_runbook_policies() -> dict[str, dict[str, Any]]:
    with _policy_path().open(encoding="utf-8") as policy_file:
        document = yaml.safe_load(policy_file) or {}
    return document.get("runbooks", {})


def evaluate_action(
    runbook_name: str,
    params: dict[str, Any],
    actor_role: UserRole | str,
    *,
    approved: bool = False,
    dry_run: bool = True,
    now: datetime | None = None,
) -> PolicyDecision:
    policies = load_runbook_policies()
    policy = policies.get(runbook_name)
    if policy is None:
        return PolicyDecision("deny", "Runbook is not declared in policy YAML", "unknown", "none", [], dry_run, False)

    role = actor_role.value if isinstance(actor_role, UserRole) else str(actor_role)
    missing = [key for key in policy.get("preconditions", []) if not params.get(key)]
    if missing:
        return PolicyDecision(
            "deny",
            f"Missing preconditions: {', '.join(missing)}",
            policy["risk_tier"],
            policy["blast_radius"],
            policy.get("rollback_steps", []),
            dry_run,
            False,
        )

    current_time = now or datetime.now()
    allowed = False
    for window in policy.get("allowed_hours", []):
        start, end = (datetime.strptime(value, "%H:%M").time() for value in window.split("-", 1))
        if start <= current_time.time() <= end:
            allowed = True
            break
    if not allowed:
        return PolicyDecision("deny", "Action is outside its allowed hours", policy["risk_tier"], policy["blast_radius"], policy.get("rollback_steps", []), dry_run, False)

    if dry_run:
        return PolicyDecision("allow", "Dry-run requested; no state change is permitted", policy["risk_tier"], policy["blast_radius"], policy.get("rollback_steps", []), True, False)

    required_role = policy["required_approver_role"]
    if not approved:
        return PolicyDecision("needs_approval", f"Explicit approval from {required_role} is required", policy["risk_tier"], policy["blast_radius"], policy.get("rollback_steps", []), False, False)
    if role != required_role and role != UserRole.ADMIN.value:
        return PolicyDecision("deny", f"Actor role {role} cannot approve this action; required role is {required_role}", policy["risk_tier"], policy["blast_radius"], policy.get("rollback_steps", []), False, False)

    return PolicyDecision("allow", "Policy conditions and approval satisfied", policy["risk_tier"], policy["blast_radius"], policy.get("rollback_steps", []), False, True)
