"""Tests for the Automated Diagnostics & Remediation Runbooks."""
from app.services.runbooks import (
    RunbookStatus,
    execute_runbook,
    get_available_runbooks,
    recommend_runbooks,
)


def test_available_runbooks_not_empty() -> None:
    """Registry should contain at least 5 runbooks."""
    runbooks = get_available_runbooks()
    assert len(runbooks) >= 5
    assert all("name" in rb and "description" in rb for rb in runbooks)


def test_reset_ad_password_blocked_without_verification() -> None:
    """Password reset should be BLOCKED when identity is not verified."""
    result = execute_runbook("reset_ad_password", {"user_id": "jdoe", "identity_verified": False})
    assert result.status == RunbookStatus.BLOCKED
    assert result.requires_approval is True
    assert "Identity" in result.actions[0]


def test_reset_ad_password_simulated_with_verification() -> None:
    """Password reset should succeed (simulated) when identity is verified."""
    result = execute_runbook("reset_ad_password", {"user_id": "jdoe", "identity_verified": True})
    assert result.status == RunbookStatus.SIMULATED
    assert result.requires_approval is False
    d = result.to_dict()
    assert d["details"]["temporary_password_set"] is True


def test_flush_vpn_sessions() -> None:
    result = execute_runbook("flush_vpn_sessions", {"user_id": "jdoe"})
    assert result.status == RunbookStatus.SIMULATED
    assert result.to_dict()["details"]["sessions_terminated"] == 2


def test_restart_print_spooler() -> None:
    result = execute_runbook("restart_print_spooler", {"device_id": "ASSET-001"})
    assert result.status == RunbookStatus.SIMULATED
    assert "ASSET-001" in " ".join(result.actions)


def test_clear_browser_cache() -> None:
    result = execute_runbook("clear_browser_cache", {"device_id": "PC-100", "browser": "Edge"})
    assert result.status == RunbookStatus.SIMULATED
    assert result.to_dict()["details"]["browser"] == "Edge"


def test_restart_endpoint_service_skipped_without_name() -> None:
    """Should skip if no service_name provided."""
    result = execute_runbook("restart_endpoint_service", {"device_id": "PC-100"})
    assert result.status == RunbookStatus.SKIPPED


def test_restart_endpoint_service_with_name() -> None:
    result = execute_runbook("restart_endpoint_service", {"device_id": "PC-100", "service_name": "wuauserv"})
    assert result.status == RunbookStatus.SIMULATED


def test_system_health_check() -> None:
    result = execute_runbook("system_health_check", {"target": "dc-01"})
    assert result.status == RunbookStatus.SIMULATED
    assert result.to_dict()["details"]["overall_status"] == "nominal"


def test_unknown_runbook_fails() -> None:
    result = execute_runbook("nonexistent_runbook", {})
    assert result.status == RunbookStatus.FAILED
    assert "Unknown" in result.to_dict()["details"]["error"]


def test_recommend_runbooks_p1_returns_empty() -> None:
    """P1/P2 incidents should NOT auto-recommend runbooks (HITL only)."""
    assert recommend_runbooks("access", "P1") == []
    assert recommend_runbooks("network", "P2") == []


def test_recommend_runbooks_p3_returns_suggestions() -> None:
    """P3/P4 should get runbook recommendations."""
    rbs = recommend_runbooks("access", "P3")
    assert "reset_ad_password" in rbs

    rbs = recommend_runbooks("network", "P4")
    assert "flush_vpn_sessions" in rbs


def test_runbook_result_to_dict_structure() -> None:
    """to_dict() output should contain all required fields."""
    result = execute_runbook("system_health_check", {})
    d = result.to_dict()
    assert "runbook_name" in d
    assert "status" in d
    assert "actions" in d
    assert "details" in d
    assert "requires_approval" in d
    assert "executed_at" in d
