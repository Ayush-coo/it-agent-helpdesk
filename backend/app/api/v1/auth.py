from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.rate_limit import failure_limiter, request_identifier
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, UserCreate
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter()


def build_auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        access_token=create_access_token(subject=user.id, role=user.role.value),
        user=UserRead.model_validate(user),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> AuthResponse:
    identifier = request_identifier(request)
    failure_limiter.check("register", identifier)
    try:
        user = await AuthService().register_user(session, payload)
    except ValueError as exc:
        failure_limiter.failure("register", identifier)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    failure_limiter.success("register", identifier)
    return build_auth_response(user)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> AuthResponse:
    identifier = request_identifier(request)
    failure_limiter.check("login", identifier)
    user = await AuthService().authenticate_user(session, payload)
    if user is None:
        failure_limiter.failure("login", identifier)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    failure_limiter.success("login", identifier)
    return build_auth_response(user)


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
