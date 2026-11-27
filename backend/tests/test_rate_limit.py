import pytest
from app.core.rate_limit import FailureRateLimiter
from fastapi import HTTPException


def test_failure_limiter_locks_after_five_failures_and_resets_on_success() -> None:
    limiter = FailureRateLimiter(
        failure_limit=5,
        window_seconds=60,
        lockout_seconds=60,
    )
    for _ in range(4):
        limiter.failure("login", "client-1")
        limiter.check("login", "client-1")

    limiter.failure("login", "client-1")
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("login", "client-1")
    assert exc_info.value.status_code == 429

    limiter.success("login", "client-1")
    limiter.check("login", "client-1")


def test_failure_limits_are_scoped_by_operation_and_identifier() -> None:
    limiter = FailureRateLimiter(
        failure_limit=1,
        window_seconds=60,
        lockout_seconds=60,
    )
    limiter.failure("otp", "user-1")

    with pytest.raises(HTTPException):
        limiter.check("otp", "user-1")
    limiter.check("otp", "user-2")
    limiter.check("chat", "user-1")
