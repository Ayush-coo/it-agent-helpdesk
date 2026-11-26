from app.models.user import User, UserRole
from fastapi import HTTPException, status

# Runbook permission matrix
RUNBOOK_PERMISSIONS = {
    "check_system_health": {UserRole.USER, UserRole.AGENT, UserRole.ADMIN},
    "clear_browser_cache": {UserRole.USER, UserRole.AGENT, UserRole.ADMIN},
    "flush_vpn_sessions": {UserRole.AGENT, UserRole.ADMIN},
    "restart_print_spooler": {UserRole.AGENT, UserRole.ADMIN},
    "reset_ad_password": {UserRole.AGENT, UserRole.ADMIN},
    "restart_endpoint_service": {UserRole.ADMIN},
}


def require_rbac_for_runbook(runbook_name: str, user: User) -> bool:
    """
    Verifies if a user has permission to execute a specific runbook based on their role.
    Raises an HTTPException if unauthorized.
    """
    allowed_roles = RUNBOOK_PERMISSIONS.get(runbook_name)
    
    if allowed_roles is None:
        # Unknown runbooks require Admin by default for safety
        allowed_roles = {UserRole.ADMIN}

    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User role '{user.role.value}' is not authorized to execute runbook '{runbook_name}'"
        )
        
    return True
