import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import settings


async def init_db() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    alembic_config = Config(str(backend_root / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(backend_root / "alembic"))
    alembic_config.set_main_option("sqlalchemy.url", settings.database_url)
    # Run the synchronous Alembic upgrade in a background thread to avoid
    # interfering with the running asyncio event loop used by the app.
    await asyncio.to_thread(command.upgrade, alembic_config, "head")
