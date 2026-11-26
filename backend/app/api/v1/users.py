from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead, UserRoleUpdate
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("", response_model=list[UserRead], dependencies=[Depends(require_roles(UserRole.ADMIN))])
async def list_users(
    session: AsyncSession = Depends(get_db),
) -> list[UserRead]:
    users = await UserRepository().list_all(session)
    return [UserRead.model_validate(user) for user in users]


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    repository = UserRepository()
    user = await repository.get_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    old_role = user.role
    if old_role != payload.role:
        user.role = payload.role
        await AuditService.log_action(
            session=session,
            user=current_user,
            action="user.role_update",
            resource_type="user",
            resource_id=user.id,
            request_payload={"old_role": old_role.value, "new_role": payload.role.value},
            status="success",
        )
        await session.commit()
        await session.refresh(user)
    return UserRead.model_validate(user)
