
"""FastAPI dependencies for route handlers."""

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.repositories.campaign_store import InMemoryCampaignStore
from app.services.campaign_service import CampaignService


def get_app_settings() -> Settings:
    """Return cached application settings."""
    return get_settings()


def get_start_time_monotonic(request: Request) -> float:
    """Return the monotonic application start timestamp."""
    return getattr(request.app.state, "start_time_monotonic", 0.0)


def get_campaign_store(request: Request) -> InMemoryCampaignStore:
    """Return the application's central in-memory campaign store."""
    app_obj = getattr(request, "app", request)
    app_state = getattr(app_obj, "state", None)
    store = getattr(app_state, "campaign_store", None) if app_state else None
    if store is None:
        # Fallback if accessed outside lifespan (e.g. lightweight testing)
        store = InMemoryCampaignStore()
        if app_state:
            app_state.campaign_store = store
    return store


def get_campaign_service(
    store: InMemoryCampaignStore = Depends(get_campaign_store),
) -> CampaignService:
    """Return the campaign business service backed by the shared in-memory store."""
    return CampaignService(store=store)


def get_active_campaigns_count(
    request: Request,
    service: CampaignService = Depends(get_campaign_service),
) -> int:
    """Return the current active campaign count (PENDING or RUNNING) in RAM."""
    if service is not None:
        return service.count_active_campaigns()
    return getattr(request.app.state, "active_campaigns_count", 0)