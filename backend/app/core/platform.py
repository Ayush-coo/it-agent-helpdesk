import asyncio
import sys


def configure_platform() -> None:
    """Use a selector loop on Windows so async database drivers remain compatible."""
    if sys.platform == "win32" and hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
