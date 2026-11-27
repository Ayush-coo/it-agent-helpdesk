from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.api.v1.admin import _average_response_minutes


def test_average_response_time_uses_first_real_staff_event_per_ticket() -> None:
    created = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    rows = [
        (SimpleNamespace(ticket_id="one", created_at=created + timedelta(minutes=10)), created),
        (SimpleNamespace(ticket_id="one", created_at=created + timedelta(minutes=30)), created),
        (SimpleNamespace(ticket_id="two", created_at=created + timedelta(minutes=20)), created),
    ]

    assert _average_response_minutes(rows) == 15
    assert _average_response_minutes([]) is None
