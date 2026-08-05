from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from app.services.ticket_service import TicketService

router = APIRouter()


def to_ticket_read(ticket) -> TicketRead:
    return TicketRead.model_validate(ticket)


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    ticket = await TicketService().create_ticket(session, payload, current_user)
    return to_ticket_read(ticket)


@router.get("", response_model=list[TicketRead])
async def list_tickets(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketRead]:
    tickets = await TicketService().list_tickets(session, current_user)
    return [to_ticket_read(ticket) for ticket in tickets]


@router.get("/{ticket_id}", response_model=TicketRead)
async def get_ticket(
    ticket_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    ticket = await TicketService().get_ticket(session, ticket_id, current_user)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return to_ticket_read(ticket)


@router.patch("/{ticket_id}", response_model=TicketRead)
async def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    ticket = await TicketService().update_ticket(session, ticket_id, payload, current_user)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return to_ticket_read(ticket)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles(UserRole.ADMIN))])
async def delete_ticket(ticket_id: str, session: AsyncSession = Depends(get_db)) -> None:
    deleted = await TicketService().delete_ticket(session, ticket_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
