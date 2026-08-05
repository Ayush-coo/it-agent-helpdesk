# AI-Powered IT Helpdesk Agent

Milestone 1 scaffold for a local-first AI helpdesk platform.

## Layout

- `backend/` FastAPI service
- `frontend/` React + TypeScript app
- `docker-compose.yml` local deployment stack with PostgreSQL

## Milestone 2

- JWT auth is available through `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, and `GET /api/v1/auth/me`.
- The backend can boot against the local SQLite default for direct VS Code runs, or against PostgreSQL through Docker Compose.

## Run locally

1. Copy `.env.example` to `.env`.
2. Start the backend from `backend/` with `uvicorn app.main:app --reload`.
3. Start the frontend from `frontend/` with `npm install` and `npm run dev`.

## Run with Docker

```bash
docker compose up --build
```

### Notes
- Use `docker compose up --build -d` to run detached.
- If `docker` is not installed on your machine, follow the "Run locally" steps below instead.

## Tests

Run backend tests from the `backend/` directory to ensure imports resolve:

```bash
cd backend
python -m pytest -q tests
```

## Troubleshooting
- If tests error with `ModuleNotFoundError: No module named 'app'`, ensure you run pytest from `backend/` so `app` is on `PYTHONPATH`.
- If you see Docker errors like "CommandNotFoundException: docker", install Docker Desktop and retry the Docker commands.

## Next steps I can take
- Add `start-dev.ps1` and `start-dev.sh` convenience scripts to boot backend+frontend locally.
- Add a `Makefile` with common targets.
- Improve `docker-compose.yml` services (healthchecks, volume names).

Tell me which next step you want me to do and I'll implement it.
