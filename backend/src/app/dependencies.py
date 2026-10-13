
"""FastAPI dependencies for route handlers."""

from fastapi import Request

from app.core.config import Settings, get_settings


def get_app_settings() -> Settings:
    """Return cached application settings."""
    return get_settings()


def get_start_time_monotonic(request: Request) -> float:
    """Return the monotonic application start timestamp."""
    return getattr(request.app.state, "start_time_monotonic", 0.0)


def get_active_campaigns_count(request: Request) -> int:
    """Return the current active campaign count."""
    return getattr(request.app.state, "active_campaigns_count", 0)