from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status

from app.core.config import settings


@dataclass
class _FailureState:
    count: int
    window_expires_at: float
    locked_until: float | None = None


class FailureRateLimiter:
    def __init__(
        self,
        *,
        failure_limit: int,
        window_seconds: int,
        lockout_seconds: int,
    ) -> None:
        self._failure_limit = failure_limit
        self._window_seconds = window_seconds
        self._lockout_seconds = lockout_seconds
        self._states: dict[tuple[str, str], _FailureState] = {}
        self._lock = Lock()

    def check(self, scope: str, identifier: str) -> None:
        now = monotonic()
        key = (scope, identifier)
        with self._lock:
            state = self._states.get(key)
            if state is None:
                return
            if state.locked_until is not None and now < state.locked_until:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed attempts. Try again later.",
                )
            if now >= state.window_expires_at or (
                state.locked_until is not None and now >= state.locked_until
            ):
                del self._states[key]

    def failure(self, scope: str, identifier: str) -> None:
        now = monotonic()
        key = (scope, identifier)
        with self._lock:
            state = self._states.get(key)
            if state is None or now >= state.window_expires_at:
                state = _FailureState(0, now + self._window_seconds)
                self._states[key] = state
            state.count += 1
            if state.count >= self._failure_limit:
                state.locked_until = now + self._lockout_seconds

    def success(self, scope: str, identifier: str) -> None:
        with self._lock:
            self._states.pop((scope, identifier), None)


failure_limiter = FailureRateLimiter(
    failure_limit=settings.auth_failure_limit,
    window_seconds=settings.auth_failure_window_minutes * 60,
    lockout_seconds=settings.auth_lockout_minutes * 60,
)


def request_identifier(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"
