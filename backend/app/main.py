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


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    yield


app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    description="AI-Powered IT Helpdesk Agent backend",
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
