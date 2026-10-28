from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import httpx


class NotificationAdapter(Protocol):
    async def send(self, message: str) -> bool: ...


@dataclass
class MockNotifier:
    messages: list[str] = field(default_factory=list)

    async def send(self, message: str) -> bool:
        self.messages.append(message)
        return True


@dataclass
class SlackWebhookNotifier:
    webhook_url: str
    fallback: NotificationAdapter

    async def send(self, message: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(self.webhook_url, json={"text": message})
                response.raise_for_status()
            return True
        except httpx.HTTPError:
            return await self.fallback.send(message)


def build_notifier(webhook_url: str | None) -> NotificationAdapter:
    fallback = MockNotifier()
    return SlackWebhookNotifier(webhook_url, fallback) if webhook_url else fallback
