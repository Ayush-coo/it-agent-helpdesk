from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket


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

    async def delete(self, session: AsyncSession, ticket: Ticket) -> None:
        await session.delete(ticket)
        await session.flush()
