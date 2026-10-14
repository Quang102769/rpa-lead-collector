"""
Central API Router Aggregation.

Organizes all endpoints according to docs/api-contract.md Section 3.2:
- Canonical Prefix: /api/v1/... (official recommended endpoints)
- Alias Prefix: /api/... (backward-compatible endpoints for direct invocation)
"""

from fastapi import APIRouter
from app.api.v1 import campaigns as campaigns_v1
from app.api.v1 import health as health_v1
from app.api.v1 import provinces as provinces_v1

# Base API Router (mounted at /api in app/main.py)
api_router = APIRouter()
v1_router = APIRouter(prefix="/v1")

# Canonical v1 routes (/api/v1/...)
v1_router.include_router(campaigns_v1.router)
v1_router.include_router(health_v1.router)
v1_router.include_router(provinces_v1.router)

# Mount canonical v1 routes under /api
api_router.include_router(v1_router)

# Alias routes (/api/...) for backward compatibility
api_router.include_router(campaigns_v1.router)
api_router.include_router(health_v1.router)
api_router.include_router(provinces_v1.router)


