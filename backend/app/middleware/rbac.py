from app.models.user import User, UserRole
from app.services.policy_engine import load_runbook_policies
from fastapi import HTTPException, status


def require_rbac_for_runbook(runbook_name: str, user: User) -> bool:
    """
    Verifies if a user has permission to execute a specific runbook based on their role.
    Raises an HTTPException if unauthorized.
    """
    policy = load_runbook_policies().get(runbook_name)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Runbook '{runbook_name}' is not declared in policy",
        )
    allowed_roles = {
        UserRole(role)
        for role in policy.get("allowed_roles", [])
        if role in {item.value for item in UserRole}
    }

    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User role '{user.role.value}' is not authorized to execute runbook '{runbook_name}'"
        )
        
    return True
