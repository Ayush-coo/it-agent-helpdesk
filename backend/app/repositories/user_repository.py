from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    async def get_by_id(self, session: AsyncSession, user_id: str) -> User | None:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        normalized_email = email.lower().strip()
        result = await session.execute(select(User).where(User.email == normalized_email))
        return result.scalar_one_or_none()

    async def add(self, session: AsyncSession, user: User) -> User:
        session.add(user)
        await session.flush()
        return user

    async def list_all(self, session: AsyncSession) -> list[User]:
        result = await session.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    async def list_assignable(self, session: AsyncSession) -> list[User]:
        result = await session.execute(
            select(User)
            .where(User.is_active.is_(True), User.role.in_([UserRole.AGENT, UserRole.ADMIN]))
            .order_by(User.full_name, User.email)
        )
        return list(result.scalars().all())
