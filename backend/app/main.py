from contextlib import asynccontextmanager

from fastapi import Request
from fastapi.responses import PlainTextResponse
from opentelemetry import trace

from app.core.platform import configure_platform

configure_platform()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.metrics import prometheus_text, record_request
from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.chat_service import ChatService
from app.services.knowledge_base_service import KnowledgeBaseService


async def ensure_development_admin() -> None:
    if settings.environment.lower() not in {"development", "dev"}:
        return
    admin_email = settings.admin_email
    admin_password = settings.admin_password
    if not admin_email and not admin_password:
        return
    if not admin_email or not admin_password:
        raise ValueError("ADMIN_EMAIL and ADMIN_PASSWORD must both be configured")

    email = admin_email.lower().strip()
    async with AsyncSessionLocal() as session:
        existing = await UserRepository().get_by_email(session, email)
        if existing is None:
            session.add(
                User(
                    full_name="Local Administrator",
                    email=email,
                    password_hash=hash_password(admin_password),
                    role=UserRole.ADMIN,
                )
            )
            await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    await ensure_development_admin()
    app.state.knowledge_base_service = KnowledgeBaseService()
    app.state.chat_service = ChatService(app.state.knowledge_base_service)
    yield


app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    description="Local-first, policy-gated IT operations backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)
_tracer = trace.get_tracer("localops-helpdesk")


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    with _tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
        response = await call_next(request)
        span.set_attribute("http.status_code", response.status_code)
    record_request(request.method, request.url.path, response.status_code)
    return response


@app.get("/metrics", include_in_schema=False)
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(prometheus_text(), media_type="text/plain; version=0.0.4")


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {
        "service": settings.project_name,
        "status": "running",
        "docs": "/docs",
    }
