from typing import Protocol


class IdentityProvider(Protocol):
    async def verify_otp(self, user_id: str, purpose: str, code: str) -> bool: ...

    async def reset_password(self, user_id: str) -> str: ...

    async def unlock_account(self, user_id: str) -> str: ...


class FakeIdentityProvider:
    """Local identity adapter. Replace this implementation with an AD/Entra adapter."""

    mock_otp = "246810"

    async def verify_otp(self, user_id: str, purpose: str, code: str) -> bool:
        del user_id, purpose
        return code == self.mock_otp

    async def reset_password(self, user_id: str) -> str:
        return f"Password reset completed for account {user_id}."

    async def unlock_account(self, user_id: str) -> str:
        return f"Account {user_id} unlocked."
