import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_chat_service, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.workspace_service import WorkspaceService

router = APIRouter()


class WorkspaceToolRequest(BaseModel):
    operation: str = Field(pattern="^(read_file|search)$")
    path: str = Field(default=".", max_length=240)
    query: str | None = Field(default=None, max_length=200)


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    from app.services.audit_service import AuditService
    try:
        reply = await service.get_reply(payload, current_user, session)
        await AuditService.log_action(
            session=session,
            user=current_user,
            action="chat.reply",
            resource_type="chat",
            request_payload={
                "message": payload.message,
                "ticket_id": payload.ticket_id,
                "conversation_id": payload.conversation_id,
            },
            status="success",
        )
        await session.commit()
        return reply
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:

    async def event_stream():
        try:
            async for event in service.stream_reply(payload, current_user):
                yield event
        except RuntimeError as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/workspace", response_model=dict[str, object])
async def workspace_tool(
    payload: WorkspaceToolRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    del current_user
    service = WorkspaceService()
    try:
        if payload.operation == "read_file":
            return service.read_file(payload.path)
        return service.search(payload.query or "", payload.path)
    except (OSError, UnicodeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc