"""Seed demo users and tickets without touching the knowledge base.

Run with: python backend/scripts/seed_users.py
"""
import asyncio
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

# Ensure the `backend` folder is on sys.path when running this script directly
backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

from app.db.session import AsyncSessionLocal
from app.schemas.auth import UserCreate
from app.schemas.ticket import TicketCreate
from app.services.auth_service import AuthService
from app.services.ticket_service import TicketService
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


async def ensure_user(
    session: AsyncSession,
    auth: AuthService,
    user_data: dict[str, Any],
    role: UserRole,
) -> User:
    repository = UserRepository()
    user = await repository.get_by_email(session, user_data["email"])
    if user is None:
        user = await auth.register_user(session, UserCreate(**user_data))
    if user.role != role:
        user.role = role
        await session.commit()
        await session.refresh(user)
    return user


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        auth = AuthService()
        ticket_svc = TicketService()

        users = [
            ({"full_name": "Demo User", "email": "demo.user@example.com", "password": "Password123"}, UserRole.USER),
            ({"full_name": "Support Agent", "email": "agent@example.com", "password": "Password123"}, UserRole.AGENT),
        ]

        seeded_users = []
        for user_data, role in users:
            try:
                user = await ensure_user(session, auth, user_data, role)
                seeded_users.append(user)
                print(f"Ensured user: {user.email} ({user.role.value})")
            except Exception as exc:
                print(f"Failed to ensure user {user_data['email']}: {exc}")

        requester = next((u for u in seeded_users if u.email == "demo.user@example.com"), None)
        if requester:
            tickets = [
                {"title": "Cannot connect to VPN", "description": "VPN connection fails with timeout when trying to connect to office network.", "priority": "high", "category": "network"},
                {"title": "Email not syncing", "description": "Outlook is not receiving new emails since last update.", "priority": "medium", "category": "email"},
                {"title": "Laptop overheating", "description": "Laptop fan runs loudly and device gets hot after 10 minutes of use.", "priority": "medium", "category": "hardware"},
            ]

            for t in tickets:
                try:
                    ticket = await ticket_svc.create_ticket(session, TicketCreate(**t), requester)
                    print(f"Created ticket: {ticket.id} - {ticket.title}")
                except Exception as exc:
                    print(f"Failed to create ticket {t['title']}: {exc}")


if __name__ == "__main__":
    asyncio.run(seed())
