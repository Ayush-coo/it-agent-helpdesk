import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_default_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(environment="production", jwt_secret_key="change-me-in-production")


def test_production_accepts_explicit_jwt_secret() -> None:
    settings = Settings(environment="production", jwt_secret_key="a-long-random-production-secret")

    assert settings.environment == "production"
