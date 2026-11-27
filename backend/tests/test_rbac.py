from types import SimpleNamespace

import pytest
from app.middleware.rbac import require_rbac_for_runbook
from app.models.user import UserRole
from app.services.policy_engine import load_runbook_policies
from app.services.runbooks import get_available_runbooks
from fastapi import HTTPException


def test_runbook_permissions_come_from_policy_yaml() -> None:
    policy = load_runbook_policies()
    registry_names = {runbook["name"] for runbook in get_available_runbooks()}
    assert registry_names == set(policy)
    for runbook_name, runbook_policy in policy.items():
        for role in runbook_policy["allowed_roles"]:
            assert require_rbac_for_runbook(
                runbook_name,
                SimpleNamespace(role=UserRole(role)),
            )


def test_system_health_check_policy_name_is_consistent() -> None:
    assert "system_health_check" in load_runbook_policies()
    assert require_rbac_for_runbook(
        "system_health_check",
        SimpleNamespace(role=UserRole.USER),
    )


def test_undeclared_runbook_is_denied() -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_rbac_for_runbook(
            "unknown_runbook",
            SimpleNamespace(role=UserRole.ADMIN),
        )
    assert exc_info.value.status_code == 403
