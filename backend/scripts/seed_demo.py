"""Seed demo data: users, tickets, and knowledge-base entries.

Run with: python backend/scripts/seed_demo.py
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
from app.schemas.knowledge_base import KnowledgeBaseIngestRequest
from app.services.auth_service import AuthService
from app.services.ticket_service import TicketService
from app.services.knowledge_base_service import KnowledgeBaseService


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        auth = AuthService()
        ticket_svc = TicketService()
        kb = KnowledgeBaseService()

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

        # Create sample tickets for demo.user@example.com
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

        # Ingest a few knowledge-base documents
        kb_docs = [
            {
                "title": "Reset VPN connection on Windows",
                "content": "To reset the VPN connection on Windows, open Settings > Network & Internet > VPN, remove the existing profile and re-add it. If using company client, ensure latest version is installed.",
                "source": "internal-article",
                "tags": ["vpn", "network"],
            },
            {
                "title": "Fix Outlook sync issues",
                "content": "When Outlook is not syncing, try clearing the cache, restart the app, and check account settings. For persistent issues, recreate the profile or contact support.",
                "source": "kb",
                "tags": ["email", "outlook"],
            },
            {
                "title": "Laptop overheating troubleshooting",
                "content": "Ensure vents are clear, update BIOS and drivers, check running processes for high CPU, and consider replacing the thermal paste if hardware is old.",
                "source": "kb",
                "tags": ["hardware", "laptop"],
            },
        ]

        for doc in kb_docs:
            try:
                ing = KnowledgeBaseIngestRequest(**doc)
                result = kb.ingest(ing)
                print(f"Ingested KB doc: {result.id} - {result.title}")
            except Exception as exc:
                print(f"KB ingest failed (continuing): {exc}")


if __name__ == "__main__":
    asyncio.run(seed())
