"""Automated Diagnostics & Remediation Runbooks.

This module provides safe, auditable runbook handlers that simulate
enterprise system API interactions. Each runbook:
  - Validates preconditions
  - Executes a mock action (no real system changes)
  - Returns a structured result with status, actions taken, and audit trail
  - Respects HITL guardrails for destructive operations

In production, these would interface with real APIs:
  Active Directory, VPN gateways, SCCM/Intune, print servers, etc.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any


class RunbookStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"          # Requires HITL approval
    SKIPPED = "skipped"          # Precondition not met
    SIMULATED = "simulated"      # Mock mode


class RunbookResult:
    """Structured result from a runbook execution."""

    def __init__(
        self,
        runbook_name: str,
        status: RunbookStatus,
        actions: list[str],
        details: dict[str, Any] | None = None,
        requires_approval: bool = False,
    ):
        self.runbook_name = runbook_name
        self.status = status
        self.actions = actions
        self.details = details or {}
        self.requires_approval = requires_approval
        self.executed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "runbook_name": self.runbook_name,
            "status": self.status.value,
            "actions": self.actions,
            "details": self.details,
            "requires_approval": self.requires_approval,
            "executed_at": self.executed_at,
        }


# ---------------------------------------------------------------------------
# Runbook Registry
# ---------------------------------------------------------------------------

_RUNBOOK_REGISTRY: dict[str, Any] = {}


def _register(name: str):
    """Decorator to register a runbook handler."""
    def decorator(func):
        _RUNBOOK_REGISTRY[name] = func
        return func
    return decorator


def get_available_runbooks() -> list[dict[str, str]]:
    """Return metadata for all registered runbooks."""
    return [
        {
            "name": name,
            "description": func.__doc__ or "No description",
        }
        for name, func in _RUNBOOK_REGISTRY.items()
    ]


def execute_runbook(name: str, params: dict[str, Any] | None = None) -> RunbookResult:
    """Execute a named runbook with optional parameters.

    This is the main entry point for the remediation engine.
    """
    handler = _RUNBOOK_REGISTRY.get(name)
    if handler is None:
        return RunbookResult(
            runbook_name=name,
            status=RunbookStatus.FAILED,
            actions=[],
            details={"error": f"Unknown runbook: {name}"},
        )
    return handler(params or {})


# ---------------------------------------------------------------------------
# Runbook Implementations (Mock / Simulated)
# ---------------------------------------------------------------------------


@_register("reset_ad_password")
def _reset_ad_password(params: dict[str, Any]) -> RunbookResult:
    """Reset an Active Directory user password after identity verification."""
    user_id = params.get("user_id", "unknown")
    verified = params.get("identity_verified", False)

    if not verified:
        return RunbookResult(
            runbook_name="reset_ad_password",
            status=RunbookStatus.BLOCKED,
            actions=[
                "Identity verification required before password reset",
                "Request MFA confirmation or manager approval",
            ],
            details={
                "target_user": user_id,
                "reason": "Identity not verified — HITL policy enforced",
            },
            requires_approval=True,
        )

    return RunbookResult(
        runbook_name="reset_ad_password",
        status=RunbookStatus.SIMULATED,
        actions=[
            "[MOCK] Connected to Active Directory domain controller",
            f"[MOCK] Located user account: {user_id}",
            "[MOCK] Generated temporary password (expires in 24h)",
            "[MOCK] Sent password reset link to registered email",
            "[MOCK] Unlocked account if previously locked",
        ],
        details={
            "target_user": user_id,
            "temporary_password_set": True,
            "account_unlocked": True,
            "password_expires_hours": 24,
            "notification_sent": True,
        },
    )


@_register("flush_vpn_sessions")
def _flush_vpn_sessions(params: dict[str, Any]) -> RunbookResult:
    """Flush active VPN sessions for a user or device to resolve connectivity issues."""
    target = params.get("user_id") or params.get("device_id", "unknown")

    return RunbookResult(
        runbook_name="flush_vpn_sessions",
        status=RunbookStatus.SIMULATED,
        actions=[
            "[MOCK] Connected to VPN gateway (Cisco AnyConnect cluster)",
            f"[MOCK] Queried active sessions for: {target}",
            "[MOCK] Found 2 stale sessions — terminated",
            "[MOCK] Cleared DTLS tunnel cache",
            "[MOCK] Verified tunnel re-establishment capability",
        ],
        details={
            "target": target,
            "sessions_terminated": 2,
            "cache_cleared": True,
            "vpn_gateway": "vpn-gw-01.corp.internal",
            "reconnection_available": True,
        },
    )


@_register("restart_print_spooler")
def _restart_print_spooler(params: dict[str, Any]) -> RunbookResult:
    """Restart the Windows Print Spooler service on a target endpoint."""
    device = params.get("device_id", "unknown")

    return RunbookResult(
        runbook_name="restart_print_spooler",
        status=RunbookStatus.SIMULATED,
        actions=[
            f"[MOCK] Connected to endpoint: {device} via WinRM",
            "[MOCK] Stopped Print Spooler service (spoolsv.exe)",
            "[MOCK] Cleared print queue (3 stuck jobs removed)",
            "[MOCK] Started Print Spooler service",
            "[MOCK] Verified service status: Running",
        ],
        details={
            "target_device": device,
            "service_name": "Spooler",
            "stuck_jobs_cleared": 3,
            "service_status": "Running",
            "response_time_ms": 1250,
        },
    )


@_register("clear_browser_cache")
def _clear_browser_cache(params: dict[str, Any]) -> RunbookResult:
    """Clear browser cache and cookies on a managed endpoint."""
    device = params.get("device_id", "unknown")
    browser = params.get("browser", "Chrome")

    return RunbookResult(
        runbook_name="clear_browser_cache",
        status=RunbookStatus.SIMULATED,
        actions=[
            f"[MOCK] Connected to endpoint: {device} via Intune",
            f"[MOCK] Identified {browser} profile data",
            "[MOCK] Cleared browser cache (245 MB freed)",
            "[MOCK] Cleared session cookies (preserved saved passwords)",
            "[MOCK] Browser restart not required",
        ],
        details={
            "target_device": device,
            "browser": browser,
            "cache_cleared_mb": 245,
            "cookies_cleared": True,
            "passwords_preserved": True,
        },
    )


@_register("restart_endpoint_service")
def _restart_endpoint_service(params: dict[str, Any]) -> RunbookResult:
    """Restart a specified Windows/Linux service on a managed endpoint."""
    device = params.get("device_id", "unknown")
    service = params.get("service_name", "unknown")

    if service == "unknown":
        return RunbookResult(
            runbook_name="restart_endpoint_service",
            status=RunbookStatus.SKIPPED,
            actions=["Service name not provided — cannot execute"],
            details={"reason": "Missing required parameter: service_name"},
        )

    return RunbookResult(
        runbook_name="restart_endpoint_service",
        status=RunbookStatus.SIMULATED,
        actions=[
            f"[MOCK] Connected to endpoint: {device}",
            f"[MOCK] Stopped service: {service}",
            "[MOCK] Waited for graceful shutdown (timeout: 30s)",
            f"[MOCK] Started service: {service}",
            "[MOCK] Health check passed",
        ],
        details={
            "target_device": device,
            "service_name": service,
            "restart_successful": True,
            "downtime_seconds": 8,
        },
    )


@_register("system_health_check")
def _check_system_health(params: dict[str, Any]) -> RunbookResult:
    """Run a comprehensive health check on a target system or endpoint."""
    target = params.get("device_id", params.get("target", "all_systems"))

    return RunbookResult(
        runbook_name="system_health_check",
        status=RunbookStatus.SIMULATED,
        actions=[
            f"[MOCK] Initiated health check for: {target}",
            "[MOCK] CPU utilization: 42% (nominal)",
            "[MOCK] Memory utilization: 68% (nominal)",
            "[MOCK] Disk I/O latency: 3.2ms (nominal)",
            "[MOCK] Network throughput: 850 Mbps (nominal)",
            "[MOCK] Active Directory replication: healthy",
            "[MOCK] DNS resolution: < 5ms (nominal)",
        ],
        details={
            "target": target,
            "cpu_percent": 42,
            "memory_percent": 68,
            "disk_io_latency_ms": 3.2,
            "network_mbps": 850,
            "ad_replication": "healthy",
            "dns_latency_ms": 4.8,
            "overall_status": "nominal",
        },
    )


# ---------------------------------------------------------------------------
# Runbook Recommendation Engine
# ---------------------------------------------------------------------------

_CATEGORY_RUNBOOK_MAP: dict[str, list[str]] = {
    "access": ["reset_ad_password"],
    "network": ["flush_vpn_sessions", "system_health_check"],
    "software": ["clear_browser_cache", "restart_endpoint_service"],
    "hardware": ["system_health_check", "restart_print_spooler"],
    "email": ["restart_endpoint_service", "system_health_check"],
    "security": [],  # Security incidents should NOT auto-remediate
    "general": ["system_health_check"],
}


def recommend_runbooks(category: str, severity: str) -> list[str]:
    """Suggest applicable runbooks based on category and severity.

    P1/P2 incidents return an empty list — they require HITL approval
    before any automated action is taken.
    """
    if severity in ("P1", "P2"):
        return []  # HITL-only — no auto-remediation
    return _CATEGORY_RUNBOOK_MAP.get(category, [])
