"""Ticket service with triage, incident detection, and escalation integration.

This service orchestrates:
  - Ticket CRUD operations
  - Automatic triage on creation (severity, category, routing)
  - Runbook recommendation and execution for P3/P4 incidents
  - HITL escalation gating for P1/P2 incidents
  - Diagnostic trail persistence
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import (
    EscalationStatus,
    SeverityLevel,
    Ticket,
    TicketComment,
    TicketEvent,
    TicketPriority,
    TicketStatus,
)
from app.models.user import User, UserRole
from app.repositories.ticket_repository import TicketRepository
from app.repositories.user_repository import UserRepository
from app.schemas.ticket import (
    EscalationAction,
    EscalationSummary,
    TicketCreate,
    TicketCommentCreate,
    TicketOverview,
    TicketRead,
    TicketStatusCount,
    TicketUpdate,
)
from app.services.ai_service import suggest_triage
from app.services.incident_detection import detect_and_link
from app.services.policy_engine import evaluate_action
from app.services.runbooks import RunbookStatus, execute_runbook, recommend_runbooks
from app.services.ticket_events import publish

# Map triage severity strings to the SeverityLevel enum
_SEVERITY_MAP = {
    "P1": SeverityLevel.P1_CRITICAL,
    "P2": SeverityLevel.P2_HIGH,
    "P3": SeverityLevel.P3_MODERATE,
    "P4": SeverityLevel.P4_LOW,
}


class TicketService:
    def __init__(self, ticket_repository: TicketRepository | None = None) -> None:
        self.ticket_repository = ticket_repository or TicketRepository()

    # ------------------------------------------------------------------
    # CREATE — with automatic triage, runbook, and escalation wiring
    # ------------------------------------------------------------------

    async def create_ticket(self, session: AsyncSession, payload: TicketCreate, current_user: User) -> Ticket:
        # 1. Run the local triage engine.
        triage = await suggest_triage(payload.description)

        severity_str = triage.get("severity", "P4")
        severity_enum = _SEVERITY_MAP.get(severity_str, SeverityLevel.P4_LOW)
        category = triage.get("category", payload.category or "general")
        diagnostic_trail = triage.get("diagnostic_trail", [])
        affected_assets = triage.get("affected_assets", [])
        requires_escalation = triage.get("requires_escalation", False)

        # 2. Determine escalation status
        escalation_status = (
            EscalationStatus.PENDING_REVIEW if requires_escalation
            else EscalationStatus.NONE
        )

        # 3. Auto-execute runbooks for P3/P4 incidents (safe actions only)
        runbook_result = None
        if not requires_escalation:
            recommended = recommend_runbooks(category, severity_str)
            if recommended:
                # Execute the first recommended runbook as a diagnostic step
                rb = execute_runbook(recommended[0], {
                    "user_id": current_user.email,
                    "device_id": next(
                        (a.split(":")[1] for a in affected_assets if a.startswith("device_id:")),
                        "auto-detected",
                    ),
                    "identity_verified": False,  # Safe default — no auto-reset
                })
                runbook_result = rb.to_dict()

                # Append runbook execution to the diagnostic trail
                diagnostic_trail.append({
                    "step": len(diagnostic_trail) + 1,
                    "action": "Runbook Execution",
                    "result": f"Executed {rb.runbook_name}: {rb.status.value}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

        # 4. Create the ticket with enriched data
        ticket = Ticket(
            ticket_number=await self.ticket_repository.allocate_ticket_number(session),
            title=payload.title.strip(),
            description=payload.description.strip(),
            priority=payload.priority,
            severity=severity_enum,
            category=category.strip() if category else None,
            requester_id=current_user.id,
            recommended_agent=None,
            diagnostic_trail=diagnostic_trail,
            affected_assets=affected_assets,
            escalation_status=escalation_status,
            runbook_result=runbook_result,
            service=payload.service.strip() if payload.service else None,
            site=payload.site.strip() if payload.site else None,
            subnet=payload.subnet.strip() if payload.subnet else None,
            asset_group=payload.asset_group.strip() if payload.asset_group else None,
        )
        await self.ticket_repository.add(session, ticket)
        await self._record_event(
            session, ticket, current_user, "created", None, ticket.title
        )
        incident_result = await detect_and_link(session, ticket)
        
        from app.services.audit_service import AuditService
        await AuditService.log_action(
            session=session,
            user=current_user,
            action="ticket.create",
            resource_type="ticket",
            resource_id=ticket.id,
            severity=severity_enum.value,
            request_payload={"title": payload.title},
            result_payload={
                "incident_id": incident_result.incident.id if incident_result.incident else None,
                "incident_similarity_mode": incident_result.similarity_mode,
                "duplicate_escalation_suppressed": incident_result.duplicate_escalation_suppressed,
            },
            status="success",
        )
        
        await session.commit()
        await session.refresh(ticket)
        publish("ticket.created")
        return ticket

    # ------------------------------------------------------------------
    # LIST / OVERVIEW
    # ------------------------------------------------------------------

    async def list_tickets(
        self,
        session: AsyncSession,
        current_user: User,
        *,
        status: TicketStatus | None = None,
        priority: TicketPriority | None = None,
        assignee_id: str | None = None,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Ticket]:
        requester_id = (
            None
            if current_user.role in {UserRole.ADMIN, UserRole.AGENT}
            else current_user.id
        )
        return await self.ticket_repository.list_filtered(
            session,
            requester_id=requester_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            q=q,
            limit=limit,
            offset=offset,
        )

    async def get_overview(self, session: AsyncSession, current_user: User) -> TicketOverview:
        if current_user.role in {UserRole.ADMIN, UserRole.AGENT}:
            tickets = await self.ticket_repository.list_all(session)
        else:
            tickets = await self.ticket_repository.list_by_requester(session, current_user.id)
        counts: dict[str, int] = {status.value: 0 for status in TicketStatus}

        for ticket in tickets:
            counts[ticket.status.value] += 1

        scope = "all tickets" if current_user.role in {UserRole.ADMIN, UserRole.AGENT} else "your tickets"

        return TicketOverview(
            scope=scope,
            total=len(tickets),
            status_counts=[TicketStatusCount(status=status, count=counts[status.value]) for status in TicketStatus],
            recent_tickets=[TicketRead.model_validate(ticket) for ticket in tickets[:8]],
            refreshed_at=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # GET / UPDATE / DELETE
    # ------------------------------------------------------------------

    async def get_ticket(self, session: AsyncSession, ticket_id: str, current_user: User) -> Ticket | None:
        ticket = await self.ticket_repository.get_by_id(session, ticket_id)
        if ticket is None:
            return None
        if not self._can_view(ticket, current_user):
            return None
        return ticket

    async def update_ticket(
        self,
        session: AsyncSession,
        ticket_id: str,
        payload: TicketUpdate,
        current_user: User,
    ) -> Ticket | None:
        ticket = await self.ticket_repository.get_by_id(session, ticket_id)
        if ticket is None:
            return None
        if not self._can_edit(ticket, current_user):
            return None

        is_staff = current_user.role in {UserRole.ADMIN, UserRole.AGENT}
        fields_set = payload.model_fields_set
        if not is_staff and fields_set.intersection(
            {"status", "priority", "severity", "assigned_to_id", "escalation_status"}
        ):
            raise PermissionError("Only agents and admins can change ticket workflow fields")
        if not is_staff and ticket.status == TicketStatus.CLOSED and fields_set:
            raise PermissionError("Closed tickets cannot be edited by requesters")
        if (
            is_staff
            and payload.status is not None
            and payload.status != ticket.status
            and payload.status not in self._STATUS_TRANSITIONS[ticket.status]
        ):
            raise ValueError(
                f"Cannot move a ticket from {ticket.status.value} to {payload.status.value}"
            )

        assigned_to_id = payload.assigned_to_id
        if is_staff and "assigned_to_id" in fields_set and assigned_to_id is not None:
            assignee = await UserRepository().get_by_id(session, assigned_to_id)
            if assignee is None or not assignee.is_active or assignee.role not in {
                UserRole.AGENT,
                UserRole.ADMIN,
            }:
                raise ValueError("Tickets can only be assigned to active agents or admins")

        changes: list[tuple[str, object, object]] = []

        def set_value(field: str, value: object) -> None:
            old_value = getattr(ticket, field)
            if old_value != value:
                setattr(ticket, field, value)
                changes.append((field, old_value, value))

        if payload.title is not None:
            set_value("title", payload.title.strip())
        if payload.description is not None:
            set_value("description", payload.description.strip())
        if payload.category is not None:
            set_value("category", payload.category.strip() if payload.category else None)

        if is_staff:
            if payload.status is not None:
                set_value("status", payload.status)
            if payload.priority is not None:
                set_value("priority", payload.priority)
            if payload.severity is not None:
                set_value("severity", payload.severity)
            if "assigned_to_id" in fields_set:
                set_value("assigned_to_id", assigned_to_id)
            if payload.escalation_status is not None:
                set_value("escalation_status", payload.escalation_status)

        for field, old_value, new_value in changes:
            await self._record_event(
                session,
                ticket,
                current_user,
                f"{field}_changed",
                self._event_value(old_value),
                self._event_value(new_value),
            )
        if changes:
            from app.services.audit_service import AuditService

            await AuditService.log_action(
                session=session,
                user=current_user,
                action="ticket.update",
                resource_type="ticket",
                resource_id=ticket.id,
                request_payload={
                    field: self._event_value(new_value)
                    for field, _, new_value in changes
                },
                status="success",
            )

        await session.commit()
        await session.refresh(ticket)
        publish("ticket.updated")
        return ticket

    async def add_comment(
        self,
        session: AsyncSession,
        ticket_id: str,
        payload: TicketCommentCreate,
        current_user: User,
    ) -> TicketComment | None:
        ticket = await self.ticket_repository.get_by_id(session, ticket_id)
        if ticket is None or not self._can_view(ticket, current_user):
            return None
        is_staff = current_user.role in {UserRole.ADMIN, UserRole.AGENT}
        if payload.is_internal and not is_staff:
            raise PermissionError("Only agents and admins can create internal comments")
        if not is_staff and ticket.status == TicketStatus.CLOSED:
            raise PermissionError("Closed tickets cannot be edited by requesters")

        comment = TicketComment(
            ticket_id=ticket.id,
            author_id=current_user.id,
            body=payload.body.strip(),
            is_internal=payload.is_internal,
        )
        await self.ticket_repository.add_comment(session, comment)
        await self._record_event(
            session,
            ticket,
            current_user,
            "internal_comment_added" if payload.is_internal else "comment_added",
            None,
            comment.id,
        )
        from app.services.audit_service import AuditService

        await AuditService.log_action(
            session=session,
            user=current_user,
            action="ticket.comment",
            resource_type="ticket",
            resource_id=ticket.id,
            request_payload={"is_internal": payload.is_internal},
            status="success",
        )
        await session.commit()
        await session.refresh(comment)
        publish("ticket.comment_added")
        return comment

    async def list_comments(
        self, session: AsyncSession, ticket_id: str, current_user: User
    ) -> list[TicketComment] | None:
        ticket = await self.ticket_repository.get_by_id(session, ticket_id)
        if ticket is None or not self._can_view(ticket, current_user):
            return None
        include_internal = current_user.role in {UserRole.ADMIN, UserRole.AGENT}
        return await self.ticket_repository.list_comments(
            session, ticket_id, include_internal=include_internal
        )

    async def list_events(
        self, session: AsyncSession, ticket_id: str, current_user: User
    ) -> list[TicketEvent] | None:
        ticket = await self.ticket_repository.get_by_id(session, ticket_id)
        if ticket is None or not self._can_view(ticket, current_user):
            return None
        events = await self.ticket_repository.list_events(session, ticket_id)
        if current_user.role not in {UserRole.ADMIN, UserRole.AGENT}:
            events = [event for event in events if event.type != "internal_comment_added"]
        return events

    async def delete_ticket(self, session: AsyncSession, ticket_id: str) -> bool:
        ticket = await self.ticket_repository.get_by_id(session, ticket_id)
        if ticket is None:
            return False
        await self.ticket_repository.delete(session, ticket)
        await session.commit()
        publish("ticket.deleted")
        return True

    # ------------------------------------------------------------------
    # HITL Escalation Flow
    # ------------------------------------------------------------------

    async def get_pending_escalations(self, session: AsyncSession) -> list[Ticket]:
        """Return all tickets with pending_review escalation status."""
        all_tickets = await self.ticket_repository.list_all(session)
        return [
            t for t in all_tickets
            if t.escalation_status == EscalationStatus.PENDING_REVIEW
        ]

    async def handle_escalation(
        self,
        session: AsyncSession,
        ticket_id: str,
        action: EscalationAction,
        current_user: User,
    ) -> Ticket | None:
        """Approve or reject a P1/P2 escalation (ADMIN/AGENT only)."""
        if current_user.role not in {UserRole.ADMIN, UserRole.AGENT}:
            return None

        ticket = await self.ticket_repository.get_by_id(session, ticket_id)
        if ticket is None:
            return None
        if ticket.escalation_status != EscalationStatus.PENDING_REVIEW:
            return None  # Can only act on pending escalations
        if (
            action.action == "approve"
            and ticket.status != TicketStatus.IN_PROGRESS
            and TicketStatus.IN_PROGRESS not in self._STATUS_TRANSITIONS[ticket.status]
        ):
            raise ValueError(
                f"Cannot move a ticket from {ticket.status.value} to {TicketStatus.IN_PROGRESS.value}"
            )

        now = datetime.now(timezone.utc).isoformat()
        trail = list(ticket.diagnostic_trail or [])

        if action.action == "approve":
            old_escalation_status = ticket.escalation_status
            ticket.escalation_status = EscalationStatus.APPROVED
            old_status = ticket.status
            ticket.status = TicketStatus.IN_PROGRESS
            if old_status != TicketStatus.IN_PROGRESS:
                await self._record_event(
                    session,
                    ticket,
                    current_user,
                    "status_changed",
                    old_status.value,
                    TicketStatus.IN_PROGRESS.value,
                )
            await self._record_event(
                session,
                ticket,
                current_user,
                "escalation_status_changed",
                old_escalation_status.value,
                EscalationStatus.APPROVED.value,
            )
            trail.append({
                "step": len(trail) + 1,
                "action": "Escalation Approved",
                "result": f"Approved by {current_user.email}. Reason: {action.reason or 'N/A'}",
                "timestamp": now,
            })
        elif action.action == "reject":
            old_escalation_status = ticket.escalation_status
            ticket.escalation_status = EscalationStatus.REJECTED
            await self._record_event(
                session,
                ticket,
                current_user,
                "escalation_status_changed",
                old_escalation_status.value,
                EscalationStatus.REJECTED.value,
            )
            trail.append({
                "step": len(trail) + 1,
                "action": "Escalation Rejected",
                "result": f"Rejected by {current_user.email}. Reason: {action.reason or 'N/A'}",
                "timestamp": now,
            })
        else:
            return None

        ticket.diagnostic_trail = trail
        await session.commit()
        await session.refresh(ticket)
        publish("ticket.escalation_updated")
        return ticket

    async def get_escalation_summary(
        self, session: AsyncSession, ticket_id: str, current_user: User,
    ) -> EscalationSummary | None:
        """Build a structured HITL handoff summary for senior engineers."""
        if current_user.role not in {UserRole.ADMIN, UserRole.AGENT}:
            return None

        ticket = await self.ticket_repository.get_by_id(session, ticket_id)
        if ticket is None:
            return None

        # Build root-cause hypothesis from the diagnostic trail
        trail = ticket.diagnostic_trail or []
        hypothesis = "Insufficient data for root-cause analysis"
        if trail:
            last_step = trail[-1]
            hypothesis = f"Based on diagnostic trail: {last_step.get('result', 'unknown')}"

        # Build recommended actions
        actions = []
        if ticket.severity in (SeverityLevel.P1_CRITICAL,):
            actions = [
                "Open incident bridge call immediately",
                "Notify VP of Engineering and affected stakeholders",
                "Engage vendor support if infrastructure is involved",
                "Begin root-cause analysis with full log collection",
            ]
        elif ticket.severity in (SeverityLevel.P2_HIGH,):
            actions = [
                "Assign to senior engineer within 15 minutes",
                "Collect relevant logs and system metrics",
                "Identify workaround to restore partial service",
                "Schedule post-incident review",
            ]

        return EscalationSummary(
            ticket_id=ticket.id,
            title=ticket.title,
            severity=ticket.severity,
            priority=ticket.priority,
            category=ticket.category,
            escalation_status=ticket.escalation_status,
            affected_assets=ticket.affected_assets,
            diagnostic_trail=ticket.diagnostic_trail,
            root_cause_hypothesis=hypothesis,
            recommended_actions=actions,
        )

    # ------------------------------------------------------------------
    # Runbook Execution (on-demand, post-creation)
    # ------------------------------------------------------------------

    async def execute_ticket_runbook(
        self,
        session: AsyncSession,
        ticket_id: str,
        runbook_name: str,
        params: dict,
        current_user: User,
        *,
        approved: bool = False,
        dry_run: bool = True,
    ) -> Ticket | None:
        """Manually trigger a runbook against a ticket (ADMIN/AGENT only)."""
        if current_user.role not in {UserRole.ADMIN, UserRole.AGENT}:
            return None

        ticket = await self.ticket_repository.get_by_id(session, ticket_id)
        if ticket is None:
            return None

        decision = evaluate_action(
            runbook_name,
            params,
            current_user.role,
            approved=approved,
            dry_run=dry_run,
        )
        if not decision.can_execute:
            result = execute_runbook(runbook_name, {})
            result.status = RunbookStatus.SIMULATED if dry_run else RunbookStatus.BLOCKED
            result.actions = [decision.reason]
            result.details = {
                "policy_decision": decision.decision,
                "risk_tier": decision.risk_tier,
                "blast_radius": decision.blast_radius,
                "rollback_steps": decision.rollback_steps,
                "dry_run": dry_run,
            }
            result.requires_approval = decision.decision == "needs_approval"
        else:
            result = execute_runbook(runbook_name, params)
            result.details["policy_decision"] = decision.decision
            result.details["dry_run"] = dry_run
        ticket.runbook_result = result.to_dict()
        await self._record_event(
            session, ticket, current_user, "runbook_executed", None, runbook_name
        )

        trail = list(ticket.diagnostic_trail or [])
        trail.append({
            "step": len(trail) + 1,
            "action": f"Manual Runbook: {runbook_name}",
            "result": f"Status: {result.status.value} | Actions: {len(result.actions)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        ticket.diagnostic_trail = trail

        await session.commit()
        await session.refresh(ticket)
        publish("ticket.runbook_executed")
        return ticket

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _can_view(self, ticket: Ticket, current_user: User) -> bool:
        return current_user.role in {UserRole.ADMIN, UserRole.AGENT} or ticket.requester_id == current_user.id

    def _can_edit(self, ticket: Ticket, current_user: User) -> bool:
        return current_user.role in {UserRole.ADMIN, UserRole.AGENT} or ticket.requester_id == current_user.id

    _STATUS_TRANSITIONS = {
        TicketStatus.OPEN: {TicketStatus.IN_PROGRESS, TicketStatus.WAITING_ON_USER},
        TicketStatus.IN_PROGRESS: {TicketStatus.WAITING_ON_USER, TicketStatus.RESOLVED},
        TicketStatus.WAITING_ON_USER: {TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED},
        TicketStatus.RESOLVED: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
        TicketStatus.CLOSED: set(),
    }

    @staticmethod
    def _event_value(value: object) -> str | None:
        if value is None:
            return None
        return str(value.value) if hasattr(value, "value") else str(value)

    @staticmethod
    async def _record_event(
        session: AsyncSession,
        ticket: Ticket,
        actor: User,
        event_type: str,
        old_value: str | None,
        new_value: str | None,
    ) -> None:
        session.add(
            TicketEvent(
                ticket_id=ticket.id,
                actor_id=actor.id,
                type=event_type,
                old_value=old_value,
                new_value=new_value,
            )
        )
