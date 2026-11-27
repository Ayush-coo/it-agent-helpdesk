import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_chat_service, get_current_user
from app.core.rate_limit import failure_limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    from app.services.audit_service import AuditService
    failure_limiter.check("chat", current_user.id)
    is_otp_attempt = payload.action_confirmation == "confirm"
    if is_otp_attempt:
        failure_limiter.check("otp", current_user.id)
    try:
        reply = await service.get_reply(payload, current_user, session)
        if is_otp_attempt:
            if reply.pending_action:
                failure_limiter.failure("otp", current_user.id)
            else:
                failure_limiter.success("otp", current_user.id)
        failure_limiter.success("chat", current_user.id)
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
        failure_limiter.failure("chat", current_user.id)
        if is_otp_attempt:
            failure_limiter.failure("otp", current_user.id)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except PermissionError as exc:
        failure_limiter.failure("chat", current_user.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    failure_limiter.check("chat", current_user.id)

    async def event_stream():
        try:
            async for event in service.stream_reply(payload, current_user):
                yield event
            failure_limiter.success("chat", current_user.id)
        except RuntimeError as exc:
            failure_limiter.failure("chat", current_user.id)
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")