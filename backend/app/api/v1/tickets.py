import asyncio

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal, get_db
from app.models.ticket import TicketPriority, TicketStatus
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.ticket import (
    TicketCommentCreate,
    TicketCommentRead,
    TicketCreate,
    TicketEventRead,
    TicketOverview,
    TicketRead,
    TicketUpdate,
)
from app.schemas.user import UserRead
from app.services.ticket_events import subscribe, unsubscribe
from app.services.ticket_service import TicketService

router = APIRouter()


def to_ticket_read(ticket) -> TicketRead:
    return TicketRead.model_validate(ticket)


async def resolve_websocket_user(token: str) -> User:
    payload = decode_access_token(token)
    subject = payload.get("sub")
    if not subject:
        raise ValueError("Invalid token payload")

    async with AsyncSessionLocal() as session:
        user = await UserRepository().get_by_id(session, subject)

    if user is None or not user.is_active:
        raise ValueError("Unauthorized")

    return user


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
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = None,
    assignee_id: str | None = None,
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketRead]:
    tickets = await TicketService().list_tickets(
        session,
        current_user,
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        q=q,
        limit=limit,
        offset=offset,
    )
    return [to_ticket_read(ticket) for ticket in tickets]


@router.get("/overview", response_model=TicketOverview)
async def get_ticket_overview(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketOverview:
    return await TicketService().get_overview(session, current_user)


@router.get(
    "/assignees",
    response_model=list[UserRead],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))],
)
async def list_ticket_assignees(
    session: AsyncSession = Depends(get_db),
) -> list[UserRead]:
    users = await UserRepository().list_assignable(session)
    return [UserRead.model_validate(user) for user in users]


@router.websocket("/overview/live")
async def stream_ticket_overview(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    try:
        current_user = await resolve_websocket_user(token)
    except Exception:
        await websocket.close(code=4401)
        return

    await websocket.accept()

    service = TicketService()
    queue = subscribe()

    try:
        async with AsyncSessionLocal() as session:
            overview = await service.get_overview(session, current_user)

        await websocket.send_json(overview.model_dump(mode="json"))

        while True:
            try:
                await asyncio.wait_for(queue.get(), timeout=30)
            except asyncio.TimeoutError:
                continue

            async with AsyncSessionLocal() as session:
                overview = await service.get_overview(session, current_user)

            await websocket.send_json(overview.model_dump(mode="json"))
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.close(code=1011)
    finally:
        unsubscribe(queue)


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


@router.post(
    "/{ticket_id}/comments",
    response_model=TicketCommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_ticket_comment(
    ticket_id: str,
    payload: TicketCommentCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketCommentRead:
    try:
        comment = await TicketService().add_comment(
            session, ticket_id, payload, current_user
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return TicketCommentRead.model_validate(comment)


@router.get("/{ticket_id}/comments", response_model=list[TicketCommentRead])
async def list_ticket_comments(
    ticket_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketCommentRead]:
    comments = await TicketService().list_comments(session, ticket_id, current_user)
    if comments is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return [TicketCommentRead.model_validate(comment) for comment in comments]


@router.get("/{ticket_id}/events", response_model=list[TicketEventRead])
async def list_ticket_events(
    ticket_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketEventRead]:
    events = await TicketService().list_events(session, ticket_id, current_user)
    if events is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return [TicketEventRead.model_validate(event) for event in events]


@router.patch("/{ticket_id}", response_model=TicketRead)
async def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    try:
        ticket = await TicketService().update_ticket(session, ticket_id, payload, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return to_ticket_read(ticket)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles(UserRole.ADMIN))])
async def delete_ticket(ticket_id: str, session: AsyncSession = Depends(get_db)) -> None:
    deleted = await TicketService().delete_ticket(session, ticket_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
