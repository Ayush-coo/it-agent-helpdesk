# IT Helpdesk Agent - Copilot instructions

## Project
AI-powered IT helpdesk. FastAPI (async) backend in backend/app, React + TypeScript
(Vite) frontend in frontend/src. SQLAlchemy 2 async + Alembic; SQLite for local runs,
PostgreSQL in Docker. LLM: Ollama (llama3.1:8b) via langchain-ollama.
RAG: Chroma + nomic-embed-text. Auth: JWT with roles (user, agent, admin).

## Architecture rules
- Layering: api/v1 routers -> services -> repositories -> models. No business logic
  in routers. Pydantic schemas live in app/schemas.
- Async handlers must never block: use httpx.AsyncClient, or run sync libraries in a threadpool.
- Every schema change needs a new Alembic migration. Never edit existing migrations.
- Config only through app/core/config.py and .env.example. No hardcoded secrets or URLs.
- Enforce roles in the service layer and with require_roles. Never trust a role sent by the client.
- LLM output is untrusted: validate it with Pydantic and always have a fallback.
- Any tool that changes data must write an audit row (ticket_events).
  Sensitive actions need explicit user confirmation.

## Quality bar
- Every change ships with tests (pytest, in-memory SQLite, mocked Ollama, no network).
- Before finishing run: `cd backend && python -m pytest -q tests` and the frontend build script.
- Small, focused diffs. Do not rename or reformat unrelated code. Do not remove features
  or change API contracts without asking.
- Full type hints in Python; no `any` in TypeScript.

## Working style
- For large changes, give a 5-bullet plan first and wait for my approval.
- End each task with: what changed, how it was verified, what is left.