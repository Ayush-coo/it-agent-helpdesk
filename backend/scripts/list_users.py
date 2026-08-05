from __future__ import annotations

import asyncio
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

from app.db.session import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select


async def main() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        if not users:
            print('No users found')
            return
        for u in users:
            print(f"{u.id} {u.email} {u.full_name} active={u.is_active} role={u.role}")


if __name__ == '__main__':
    asyncio.run(main())
