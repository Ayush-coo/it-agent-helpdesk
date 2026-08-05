"""Seed demo users and tickets without touching the knowledge base.

Run with: python backend/scripts/seed_users.py
"""
import asyncio
import sys
from pathlib import Path

# Ensure the `backend` folder is on sys.path when running this script directly
backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

from app.db.session import AsyncSessionLocal
from app.schemas.auth import UserCreate
from app.schemas.ticket import TicketCreate
from app.services.auth_service import AuthService
from app.services.ticket_service import TicketService


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        auth = AuthService()
        ticket_svc = TicketService()

        users = [
            {"full_name": "Demo User", "email": "demo.user@example.com", "password": "Password123"},
            {"full_name": "Support Agent", "email": "agent@example.com", "password": "Password123"},
        ]

        created_users = []
        for u in users:
            try:
                user = await auth.register_user(session, UserCreate(**u))
                created_users.append(user)
                print(f"Created user: {user.email} ({user.id})")
            except Exception as exc:
                print(f"Skipping user {u['email']}: {exc}")

        requester = next((u for u in created_users if u.email == "demo.user@example.com"), None)
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
