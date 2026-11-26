import httpx
from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.schemas.ai import AIStatusResponse, TriageRequest, TriageResponse
from app.services.ai_service import suggest_triage

router = APIRouter()


@router.get("/status", response_model=AIStatusResponse)
async def ai_status(_=Depends(get_current_user)) -> AIStatusResponse:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            installed_models = {model.get("name") for model in models if isinstance(model, dict)}
            if settings.ollama_model not in installed_models:
                return AIStatusResponse(
                    model=settings.ollama_model,
                    available=False,
                    detail=f"Ollama is running, but {settings.ollama_model} is not installed",
                )
            return AIStatusResponse(model=settings.ollama_model, available=True, detail="Connected")
    except Exception:
        return AIStatusResponse(
            model=settings.ollama_model,
            available=False,
            detail="Ollama is not reachable",
        )


@router.post("/suggest-triage", response_model=TriageResponse)
async def suggest_triage_endpoint(payload: TriageRequest, _=Depends(get_current_user)) -> TriageResponse:
    result = await suggest_triage(payload.description)
    return TriageResponse(
        priority=result.get("priority", "medium"),
        severity=result.get("severity", "P4"),
        category=result.get("category", "general"),
        short_summary=result.get("short_summary", payload.description[:200]),
        next_steps=result.get("next_steps", ["Review the request details"]),
        affected_assets=result.get("affected_assets", []),
        diagnostic_trail=result.get("diagnostic_trail", []),
        requires_escalation=result.get("requires_escalation", False),
    )
