from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCreate, TicketUpdate


class TicketService:
    def __init__(self, ticket_repository: TicketRepository | None = None) -> None:
        self.ticket_repository = ticket_repository or TicketRepository()

    async def create_ticket(self, session: AsyncSession, payload: TicketCreate, current_user: User) -> Ticket:
        ticket = Ticket(
            title=payload.title.strip(),
            description=payload.description.strip(),
            priority=payload.priority,
            category=payload.category.strip() if payload.category else None,
            requester_id=current_user.id,
        )
        await self.ticket_repository.add(session, ticket)
        await session.commit()
        await session.refresh(ticket)
        return ticket

    async def list_tickets(self, session: AsyncSession, current_user: User) -> list[Ticket]:
        if current_user.role in {UserRole.ADMIN, UserRole.AGENT}:
            return await self.ticket_repository.list_all(session)
        return await self.ticket_repository.list_by_requester(session, current_user.id)

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

        if current_user.role in {UserRole.ADMIN, UserRole.AGENT}:
            if payload.title is not None:
                ticket.title = payload.title.strip()
            if payload.description is not None:
                ticket.description = payload.description.strip()
            if payload.status is not None:
                ticket.status = payload.status
            if payload.priority is not None:
                ticket.priority = payload.priority
            if payload.assigned_to_id is not None:
                ticket.assigned_to_id = payload.assigned_to_id
            if payload.category is not None:
                ticket.category = payload.category.strip() if payload.category else None
        else:
            if payload.status is not None or payload.priority is not None or payload.assigned_to_id is not None:
                return None
            if payload.title is not None:
                ticket.title = payload.title.strip()
            if payload.description is not None:
                ticket.description = payload.description.strip()
            if payload.category is not None:
                ticket.category = payload.category.strip() if payload.category else None

        await session.commit()
        await session.refresh(ticket)
        return ticket

    async def delete_ticket(self, session: AsyncSession, ticket_id: str) -> bool:
        ticket = await self.ticket_repository.get_by_id(session, ticket_id)
        if ticket is None:
            return False
        await self.ticket_repository.delete(session, ticket)
        await session.commit()
        return True

    def _can_view(self, ticket: Ticket, current_user: User) -> bool:
        return current_user.role in {UserRole.ADMIN, UserRole.AGENT} or ticket.requester_id == current_user.id

    def _can_edit(self, ticket: Ticket, current_user: User) -> bool:
        return current_user.role in {UserRole.ADMIN, UserRole.AGENT} or ticket.requester_id == current_user.id
