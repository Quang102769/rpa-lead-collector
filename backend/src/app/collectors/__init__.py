"""Collectors module providing data extraction adapters and fixture loaders."""

from app.collectors.base import BaseCollector
from app.collectors.fixture_collector import FixtureCollector
from app.collectors.models import RawLeadRecord

__all__ = [
    "BaseCollector",
    "FixtureCollector",
    "RawLeadRecord",
]
