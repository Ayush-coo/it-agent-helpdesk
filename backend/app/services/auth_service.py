from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, UserCreate


class AuthService:
    def __init__(self, user_repository: UserRepository | None = None) -> None:
        self.user_repository = user_repository or UserRepository()

    async def register_user(self, session: AsyncSession, payload: UserCreate) -> User:
        existing_user = await self.user_repository.get_by_email(session, payload.email)
        if existing_user is not None:
            raise ValueError("Email is already registered")

        user = User(
            full_name=payload.full_name,
            email=payload.email.lower().strip(),
            password_hash=hash_password(payload.password),
            role=UserRole.USER,
        )
        await self.user_repository.add(session, user)
        await session.commit()
        await session.refresh(user)
        return user

    async def authenticate_user(self, session: AsyncSession, payload: LoginRequest) -> User | None:
        user = await self.user_repository.get_by_email(session, payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            return None
        return user
