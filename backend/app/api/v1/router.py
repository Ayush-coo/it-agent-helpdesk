from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router
from app.api.v1.knowledge_base import router as knowledge_base_router
from app.api.v1.tickets import router as tickets_router
from app.api.v1.ai import router as ai_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(knowledge_base_router, prefix="/knowledge-base", tags=["knowledge-base"])
api_router.include_router(tickets_router, prefix="/tickets", tags=["tickets"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
