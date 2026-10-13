"""
Central API Router Aggregation.

Organizes all endpoints according to docs/api-contract.md Section 3.2:
- Canonical Prefix: /api/v1/... (official recommended endpoints)
- Alias Prefix: /api/... (backward-compatible endpoints for direct invocation)
"""

from fastapi import APIRouter
from app.api.v1 import health as health_v1

# Base API Router (mounted at /api in app/main.py)
api_router = APIRouter()
v1_router = APIRouter(prefix="/v1")
# Health check endpoint (/api/v1/health)
v1_router.include_router(health_v1.router)
# Mount canonical v1 routes under /api
api_router.include_router(v1_router)
api_router.include_router(health_v1.router)

