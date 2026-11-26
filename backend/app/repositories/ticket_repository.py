from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import (
    Ticket,
    TicketComment,
    TicketEvent,
    TicketNumberCounter,
    TicketPriority,
    TicketStatus,
)


class TicketRepository:
    async def add(self, session: AsyncSession, ticket: Ticket) -> Ticket:
        session.add(ticket)
        await session.flush()
        return ticket

    async def get_by_id(self, session: AsyncSession, ticket_id: str) -> Ticket | None:
        result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
        return result.scalar_one_or_none()

    async def list_all(self, session: AsyncSession) -> list[Ticket]:
        result = await session.execute(select(Ticket).order_by(Ticket.created_at.desc()))
        return list(result.scalars().all())

    async def list_by_requester(self, session: AsyncSession, requester_id: str) -> list[Ticket]:
        result = await session.execute(
            select(Ticket).where(Ticket.requester_id == requester_id).order_by(Ticket.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_filtered(
        self,
        session: AsyncSession,
        requester_id: str | None = None,
        status: TicketStatus | None = None,
        priority: TicketPriority | None = None,
        assignee_id: str | None = None,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Ticket]:
        query = select(Ticket)
        if requester_id is not None:
            query = query.where(Ticket.requester_id == requester_id)
        if status is not None:
            query = query.where(Ticket.status == status)
        if priority is not None:
            query = query.where(Ticket.priority == priority)
        if assignee_id is not None:
            query = query.where(Ticket.assigned_to_id == assignee_id)
        if q:
            search = f"%{q.strip()}%"
            query = query.where(or_(Ticket.title.ilike(search), Ticket.description.ilike(search)))
        result = await session.execute(
            query.order_by(Ticket.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def allocate_ticket_number(self, session: AsyncSession) -> str:
        result = await session.execute(
            update(TicketNumberCounter)
            .where(TicketNumberCounter.id == 1)
            .values(value=TicketNumberCounter.value + 1)
            .returning(TicketNumberCounter.value)
        )
        value = result.scalar_one()
        return f"INC-{value:04d}"

    async def add_comment(self, session: AsyncSession, comment: TicketComment) -> TicketComment:
        session.add(comment)
        await session.flush()
        return comment

    async def list_comments(
        self, session: AsyncSession, ticket_id: str, include_internal: bool
    ) -> list[TicketComment]:
        query = select(TicketComment).where(TicketComment.ticket_id == ticket_id)
        if not include_internal:
            query = query.where(TicketComment.is_internal.is_(False))
        result = await session.execute(query.order_by(TicketComment.created_at.asc()))
        return list(result.scalars().all())

    async def list_events(self, session: AsyncSession, ticket_id: str) -> list[TicketEvent]:
        result = await session.execute(
            select(TicketEvent)
            .where(TicketEvent.ticket_id == ticket_id)
            .order_by(TicketEvent.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete(self, session: AsyncSession, ticket: Ticket) -> None:
        await session.delete(ticket)
        await session.flush()
