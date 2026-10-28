import asyncio

from app.integrations.slack import MockNotifier


def test_mock_notification_adapter_records_message() -> None:
    notifier = MockNotifier()

    assert asyncio.run(notifier.send("incident opened")) is True
    assert notifier.messages == ["incident opened"]
