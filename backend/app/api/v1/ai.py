from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.schemas.ai import TriageRequest, TriageResponse
from app.services.ai_service import suggest_triage

router = APIRouter()


@router.post("/suggest-triage", response_model=TriageResponse)
async def suggest_triage_endpoint(payload: TriageRequest, _=Depends(get_current_user)) -> TriageResponse:
    result = suggest_triage(payload.description)
    return TriageResponse(
        priority=result.get("priority", "medium"),
        category=result.get("category", "general"),
        short_summary=result.get("short_summary", payload.description[:200]),
        recommended_agent=result.get("recommended_agent", "classifier_agent"),
        next_steps=result.get("next_steps", ["Review the request details"]),
    )
