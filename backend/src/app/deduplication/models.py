"""Data transfer objects and models for lead deduplication stage."""

from dataclasses import dataclass, field
from enum import Enum

from app.collectors.models import RawLeadRecord


class DuplicateReason(str, Enum):
    """Reason code for deterministic lead deduplication matching."""

    NAME_AND_WEBSITE_MATCH = "NAME_AND_WEBSITE_MATCH"
    NAME_AND_PHONE_MATCH = "NAME_AND_PHONE_MATCH"
    NAME_AND_WEBSITE_AND_PHONE_MATCH = "NAME_AND_WEBSITE_AND_PHONE_MATCH"


@dataclass
class DuplicateGroup:
    """Group of duplicated lead records identified and resolved."""

    kept_record: RawLeadRecord
    removed_records: list[RawLeadRecord] = field(default_factory=list)
    reason_code: DuplicateReason | str = DuplicateReason.NAME_AND_WEBSITE_MATCH
    matched_fields: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for rec in self.removed_records:
            if rec is self.kept_record:
                raise ValueError("A group's kept_record cannot be included in its removed_records.")


@dataclass
class DeduplicationResult:
    """Aggregated result of batch lead deduplication."""

    unique_records: list[RawLeadRecord] = field(default_factory=list)
    duplicate_groups: list[DuplicateGroup] = field(default_factory=list)
    total_processed: int = 0

    def __post_init__(self) -> None:
        # 1. Validate that removed_records are not counted across multiple duplicate groups
        seen_removed_ids: set[int] = set()
        for group in self.duplicate_groups:
            for rec in group.removed_records:
                rec_id = id(rec)
                if rec_id in seen_removed_ids:
                    raise ValueError(
                        "Duplicate record detected across multiple duplicate groups or within a group."
                    )
                seen_removed_ids.add(rec_id)

        # 2. Validate that unique_records and removed_records are mutually disjoint
        unique_ids = {id(rec) for rec in self.unique_records}
        overlap = unique_ids.intersection(seen_removed_ids)
        if overlap:
            raise ValueError(
                "Inconsistent result: a record cannot appear in both unique_records and removed_records."
            )

        # 3. Validate metric counter invariant: total_processed = unique_count + duplicate_count
        expected_total = len(self.unique_records) + sum(
            len(group.removed_records) for group in self.duplicate_groups
        )
        if self.total_processed == 0 and expected_total > 0:
            self.total_processed = expected_total
        elif self.total_processed != expected_total:
            raise ValueError(
                f"Metric invariant violation: total_processed ({self.total_processed}) "
                f"must equal unique_count ({len(self.unique_records)}) + "
                f"duplicate_count ({sum(len(group.removed_records) for group in self.duplicate_groups)})."
            )


    @property
    def unique_count(self) -> int:
        """Count of retained unique records."""
        return len(self.unique_records)

    @property
    def duplicate_count(self) -> int:
        """Count of redundant duplicate records removed."""
        return sum(len(group.removed_records) for group in self.duplicate_groups)

