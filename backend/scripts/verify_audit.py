import asyncio
import json

from app.db.session import AsyncSessionLocal
from app.services.audit_verify import verify_audit_chain


async def main() -> None:
    async with AsyncSessionLocal() as session:
        print(json.dumps(await verify_audit_chain(session), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
