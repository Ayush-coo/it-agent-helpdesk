from collections.abc import Iterable
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.integrations.slack import build_notifier
from app.models.audit_log import AuditLog
from app.models.ticket import Ticket, TicketEvent, TicketStatus
from app.models.user import User, UserRole
from app.services.audit_verify import verify_audit_chain

router = APIRouter()


def _average_response_minutes(
    event_rows: Iterable[tuple[TicketEvent, datetime]],
) -> float | None:
    first_response_by_ticket = {}
    for event, ticket_created_at in event_rows:
        if event.ticket_id in first_response_by_ticket:
            continue
        response_at = event.created_at
        if response_at.tzinfo is None and ticket_created_at.tzinfo is not None:
            response_at = response_at.replace(tzinfo=response_at.tzinfo or ticket_created_at.tzinfo)
        elif response_at.tzinfo is not None and ticket_created_at.tzinfo is None:
            ticket_created_at = ticket_created_at.replace(tzinfo=response_at.tzinfo)
        first_response_by_ticket[event.ticket_id] = max(
            0.0, (response_at - ticket_created_at).total_seconds() / 60
        )
    if not first_response_by_ticket:
        return None
    return sum(first_response_by_ticket.values()) / len(first_response_by_ticket)


class NotificationRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


@router.post("/notifications/test", dependencies=[Depends(require_roles(UserRole.ADMIN))])
async def send_notification(
    payload: NotificationRequest,
    _=Depends(get_current_user),
) -> dict[str, bool]:
    sent = await build_notifier(settings.slack_webhook_url).send(payload.message)
    return {"sent": sent, "simulated": settings.slack_webhook_url is None}


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
    tickets = await session.execute(select(Ticket))
    all_tickets = tickets.scalars().all()
    open_p1_p2 = len([
        ticket
        for ticket in all_tickets
        if getattr(ticket.severity, "value", ticket.severity) in {"P1", "P2"}
        and ticket.status == TicketStatus.OPEN
    ])
    auto_resolved = len([t for t in all_tickets if t.status == TicketStatus.RESOLVED and t.runbook_result])
    response_events = await session.execute(
        select(TicketEvent, Ticket.created_at)
        .join(Ticket, TicketEvent.ticket_id == Ticket.id)
        .join(User, TicketEvent.actor_id == User.id)
        .where(
            User.role.in_([UserRole.AGENT, UserRole.ADMIN]),
            TicketEvent.type.in_([
                "comment_added",
                "status_changed",
                "assigned_to_id_changed",
                "approval_approved",
                "approval_rejected",
            ]),
        )
        .order_by(TicketEvent.created_at.asc())
    )
    average_response_minutes = _average_response_minutes(response_events.tuples().all())

    return {
        "total_tickets": len(all_tickets),
        "open_p1_p2": open_p1_p2,
        "auto_resolved_rate": f"{(auto_resolved / max(1, len(all_tickets)) * 100):.1f}%",
        "avg_response_time": (
            f"{average_response_minutes:.1f}m"
            if average_response_minutes is not None
            else "N/A"
        ),
    }
