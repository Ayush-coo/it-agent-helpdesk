"""Escalation & Runbook API Endpoints.

Provides:
  - GET  /escalations           → List all pending P1/P2 escalations
  - GET  /escalations/{id}      → Get structured HITL handoff summary
  - POST /escalations/{id}      → Approve or reject an escalation
  - GET  /runbooks              → List available runbooks
  - POST /tickets/{id}/runbook  → Execute a runbook against a ticket
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.ticket import EscalationAction, EscalationSummary, TicketRead
from app.services.runbooks import get_available_runbooks
from app.services.ticket_service import TicketService

router = APIRouter()


def to_ticket_read(ticket) -> TicketRead:
    return TicketRead.model_validate(ticket)


# ---------------------------------------------------------------------------
# Escalation Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/escalations",
    response_model=list[TicketRead],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))],
)
async def list_pending_escalations(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketRead]:
    """List all tickets with pending HITL escalation review."""
    tickets = await TicketService().get_pending_escalations(session)
    return [to_ticket_read(t) for t in tickets]


@router.get(
    "/escalations/{ticket_id}",
    response_model=EscalationSummary,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))],
)
async def get_escalation_summary(
    ticket_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EscalationSummary:
    """Get a structured HITL handoff summary for senior engineers."""
    summary = await TicketService().get_escalation_summary(session, ticket_id, current_user)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or access denied",
        )
    return summary


@router.post(
    "/escalations/{ticket_id}",
    response_model=TicketRead,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))],
)
async def handle_escalation(
    ticket_id: str,
    action: EscalationAction,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    """Approve or reject a P1/P2 escalation."""
    if action.action not in ("approve", "reject"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'approve' or 'reject'",
        )
    ticket = await TicketService().handle_escalation(session, ticket_id, action, current_user)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found, not pending review, or access denied",
        )
        
    from app.services.audit_service import AuditService
    await AuditService.log_action(
        session=session,
        user=current_user,
        action=f"escalation.{action.action}",
        resource_type="ticket",
        resource_id=ticket.id,
        severity=ticket.severity.value if ticket.severity else None,
        request_payload={"reason": action.reason},
        status="success"
    )
    await session.commit()
    await session.refresh(ticket)
        
    return to_ticket_read(ticket)


# ---------------------------------------------------------------------------
# Runbook Endpoints
# ---------------------------------------------------------------------------


class RunbookListItem(BaseModel):
    name: str
    description: str


class RunbookExecuteRequest(BaseModel):
    runbook_name: str = Field(min_length=1)
    params: dict = Field(default_factory=dict)
    approved: bool = False
    dry_run: bool = True


@router.get("/runbooks", response_model=list[RunbookListItem])
async def list_runbooks(
    _=Depends(get_current_user),
) -> list[RunbookListItem]:
    """List all available remediation runbooks."""
    return [RunbookListItem(**rb) for rb in get_available_runbooks()]


@router.post(
    "/tickets/{ticket_id}/runbook",
    response_model=TicketRead,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))],
)
async def execute_ticket_runbook(
    ticket_id: str,
    payload: RunbookExecuteRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    """Execute a named runbook against a specific ticket."""
    from app.middleware.rbac import require_rbac_for_runbook
    from app.services.audit_service import AuditService

    require_rbac_for_runbook(payload.runbook_name, current_user)
    
    ticket = await TicketService().execute_ticket_runbook(
        session,
        ticket_id,
        payload.runbook_name,
        payload.params,
        current_user,
        approved=payload.approved,
        dry_run=payload.dry_run,
    )
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or access denied",
        )
        
    await AuditService.log_action(
        session=session,
        user=current_user,
        action="runbook.execute",
        resource_type="ticket",
        resource_id=ticket.id,
        tool_called=payload.runbook_name,
        request_payload=payload.params,
        status="success"
    )
    await session.commit()
    await session.refresh(ticket)
        
    return to_ticket_read(ticket)
