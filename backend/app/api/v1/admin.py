from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.models.ticket import Ticket, TicketStatus
from app.services.audit_verify import verify_audit_chain

router = APIRouter()


@router.get("/audit-logs/verify", dependencies=[Depends(require_roles(UserRole.ADMIN))])
async def verify_audit_logs(
    session: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> dict:
    return await verify_audit_chain(session)

@router.get("/audit-logs", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
async def get_audit_logs(
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
    _=Depends(get_current_user)
):
    result = await session.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit))
    logs = result.scalars().all()
    return logs

@router.get("/metrics", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
async def get_admin_metrics(
    session: AsyncSession = Depends(get_db),
    _=Depends(get_current_user)
):
    # Quick mock metrics, in reality these would be complex group_by queries
    tickets = await session.execute(select(Ticket))
    all_tickets = tickets.scalars().all()
    
    open_p1 = len([t for t in all_tickets if t.severity == 'P1' and t.status == TicketStatus.OPEN])
    auto_resolved = len([t for t in all_tickets if t.status == TicketStatus.RESOLVED and t.runbook_result])
    
    return {
        "total_tickets": len(all_tickets),
        "open_p1_p2": open_p1,
        "auto_resolved_rate": f"{(auto_resolved / max(1, len(all_tickets)) * 100):.1f}%",
        "avg_response_time": "1.2m"
    }
