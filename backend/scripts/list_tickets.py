from __future__ import annotations

import asyncio
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

from app.db.session import AsyncSessionLocal
from app.models.ticket import Ticket
from sqlalchemy import select


async def main() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Ticket))
        tickets = result.scalars().all()
        if not tickets:
            print('No tickets found')
            return
        for t in tickets:
            print(f"{t.id} {t.title} requester={t.requester_id} priority={t.priority} category={t.category}")


if __name__ == '__main__':
    asyncio.run(main())
