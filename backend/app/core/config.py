import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "IT Helpdesk Agent"
    project_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    database_url: str = "sqlite+aiosqlite:///./it_agent.db"
    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_temperature: float = 0.2
    ollama_timeout_seconds: int = 60
    chroma_persist_directory: str = str(Path(__file__).resolve().parents[2] / ".chroma")
    knowledge_collection_name: str = "it_helpdesk_knowledge"
    knowledge_retrieval_k: int = 4

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _normalize_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return ["http://localhost:5173"]
        if isinstance(value, str):
            if value.strip().startswith("["):
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    parsed_value = None
                else:
                    if isinstance(parsed_value, list):
                        return [str(origin).strip() for origin in parsed_value if str(origin).strip()]
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
