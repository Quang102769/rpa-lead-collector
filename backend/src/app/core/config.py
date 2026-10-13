"""Application configuration loaded from the backend .env file."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# backend/src/app/core/config.py -> backend/
BACKEND_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Centralized configuration for the application."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_env: Literal[
        "local", "development", "staging", "production"
    ] = "local"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    debug: bool = False

    # Frontend CORS
    cors_origins: list[str] = Field(default_factory=list)

    # Execution mode
    # Keep FIXTURE as the default for the MVP.
    execution_mode: Literal["FIXTURE", "LIVE"] = "FIXTURE"

    # Approved LIVE sources. Empty means no source is approved.
    approved_live_sources: list[str] = Field(default_factory=list)

    # External LLM provider
    # Optional so the backend can run offline in FIXTURE mode.
    llm_api_key: str | None = None
    llm_api_base_url: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached application settings instance."""
    return Settings()
