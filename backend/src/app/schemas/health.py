"""Health check schemas conforming to docs/api-contract.md Section 6.6."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class HealthData(BaseModel):
    """Health status details."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["HEALTHY"] = "HEALTHY"
    service: str = "ai-rpa-lead-collector-backend"
    version: str = "1.0.0"
    environment: str = "local_mvp"
    uptime_seconds: int = Field(ge=0)
    active_campaigns_in_ram: int = Field(ge=0)
    exports_directory_accessible: bool
    timestamp: str = Field(min_length=1)


class HealthResponse(BaseModel):
    """Standard response model for GET /api/v1/health."""

    model_config = ConfigDict(extra="forbid")

    success: Literal[True] = True
    data: HealthData