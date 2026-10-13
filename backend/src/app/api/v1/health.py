"""Health check router according to API Contract specification."""

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends
from app.dependencies import (
    get_active_campaigns_count,
    get_app_settings,
    get_start_time_monotonic,
)
from app.core import constants
from app.core.config import Settings
from app.schemas.health import HealthData, HealthResponse

logger = logging.getLogger("app")

router = APIRouter(tags=["Health"])


def check_exports_directory_accessible(exports_path: Path) -> bool:
    """Safely verify that the exports directory exists or can be written to."""
    try:
        exports_path.mkdir(parents=True, exist_ok=True)
        # Test write permission
        test_file = exports_path / ".health_check_probe"
        test_file.touch(exist_ok=True)
        if test_file.exists():
            test_file.unlink(missing_ok=True)
        return True
    except Exception as exc:
        logger.warning(
            "Exports directory accessibility check failed for path %s: %s",
            exports_path,
            exc.__class__.__name__,
        )
        return False


@router.get("/health", response_model=HealthResponse, summary="Kiểm tra sức khỏe hệ thống")
async def get_health(
    settings: Settings = Depends(get_app_settings),
    start_time_monotonic: float = Depends(get_start_time_monotonic),
    active_campaigns: int = Depends(get_active_campaigns_count),
) -> HealthResponse:
    """
    Health check endpoint conforming to docs/api-contract.md Section 6.6.
    Returns liveness, runtime metadata, and disk accessibility.
    """
    now = datetime.now(timezone.utc)
    timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"

    current_monotonic = time.monotonic()
    uptime_seconds = int(current_monotonic - start_time_monotonic) if start_time_monotonic > 0 else 0

    exports_accessible = check_exports_directory_accessible(constants.EXPORTS_DIR)

    # Environment display name: fallback to local_mvp if in development
    env_display = "local_mvp" if settings.app_env in ("development", "local") else settings.app_env

    return HealthResponse(
        success=True,
        data=HealthData(
            status="HEALTHY",
            service=constants.SERVICE_NAME,
            version=constants.APP_VERSION,
            environment=env_display,
            uptime_seconds=uptime_seconds,
            active_campaigns_in_ram=active_campaigns,
            exports_directory_accessible=exports_accessible,
            timestamp=timestamp_str,
        ),
    )
