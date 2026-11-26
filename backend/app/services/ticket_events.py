from __future__ import annotations

import asyncio

_subscribers: set[asyncio.Queue[str]] = set()


def subscribe() -> asyncio.Queue[str]:
    queue: asyncio.Queue[str] = asyncio.Queue(maxsize=1)
    _subscribers.add(queue)
    return queue


def unsubscribe(queue: asyncio.Queue[str]) -> None:
    _subscribers.discard(queue)


def publish(event_type: str) -> None:
    for queue in tuple(_subscribers):
        if queue.full():
            continue

        try:
            queue.put_nowait(event_type)
        except RuntimeError:
            _subscribers.discard(queue)