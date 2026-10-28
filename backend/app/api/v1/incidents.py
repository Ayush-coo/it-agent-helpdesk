from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.incident import Incident
from app.models.user import User, UserRole
from app.schemas.incident import IncidentRead
from app.services.incident_simulator import simulate_incident_detection

router = APIRouter()


@router.get("", response_model=list[IncidentRead])
async def list_incidents(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Incident]:
    if current_user.role not in {UserRole.ADMIN, UserRole.AGENT}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent access required")
    result = await session.execute(select(Incident).order_by(Incident.last_seen_at.desc()))
    return list(result.scalars().all())


@router.get("/simulate", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
async def simulate_incidents() -> dict:
    return simulate_incident_detection()
