"""Deduplication module public exports."""

from app.deduplication.deduplicator import Deduplicator
from app.deduplication.models import (
    DeduplicationResult,
    DuplicateGroup,
    DuplicateReason,
)

__all__ = [
    "Deduplicator",
    "DeduplicationResult",
    "DuplicateGroup",
    "DuplicateReason",
]
