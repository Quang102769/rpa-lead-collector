"""Data transfer objects and models for lead validation stage."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.collectors.models import RawLeadRecord


class ValidationStatus(str, Enum):
    """Validation status classification for lead records."""

    VALID = "VALID"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"


@dataclass
class FieldError:
    """Represents a field-level error or warning."""

    field: str
    error_code: str
    message: str
    rejected_value: Any = None


@dataclass
class LeadValidationItemResult:
    """Validation result for a single raw lead record."""

    status: ValidationStatus
    lead: RawLeadRecord | None = None
    raw_lead: RawLeadRecord | None = None
    errors: list[FieldError] = field(default_factory=list)
    warnings: list[FieldError] = field(default_factory=list)


@dataclass
class ValidationBatchResult:
    """Aggregated validation result for a batch of lead records."""

    results: list[LeadValidationItemResult] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        """Total number of records evaluated."""
        return len(self.results)

    @property
    def valid_records(self) -> list[RawLeadRecord]:
        """List of sanitized lead records that can proceed in the pipeline."""
        return [
            item.lead
            for item in self.results
            if item.status in (
                ValidationStatus.VALID,
                ValidationStatus.PARTIAL,
            )
            and item.lead is not None
        ]

    @property
    def rejected_records(self) -> list[LeadValidationItemResult]:
        """List of validation items that were rejected."""
        return [
            item
            for item in self.results
            if item.status == ValidationStatus.REJECTED
        ]

    @property
    def records_valid(self) -> int:
        """Count of fully valid records with zero warnings."""
        return sum(
            item.status == ValidationStatus.VALID
            for item in self.results
        )

    @property
    def records_partial(self) -> int:
        """Count of partially valid records (degraded optional fields)."""
        return sum(
            item.status == ValidationStatus.PARTIAL
            for item in self.results
        )

    @property
    def records_rejected(self) -> int:
        """Count of rejected records."""
        return len(self.rejected_records)

    @property
    def warnings_count(self) -> int:
        """Total count of warnings accumulated across all records."""
        return sum(len(item.warnings) for item in self.results)
