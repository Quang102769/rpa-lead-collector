"""Data models for shared pipeline execution and aggregated metrics."""

from dataclasses import dataclass


@dataclass
class PipelineResult:
    """Aggregated result and metrics of an end-to-end pipeline execution.

    Invariants enforced:
    1. total_after_validation == records_valid + records_partial
    2. total_after_validation == unique_count + duplicate_count
    """

    total_collected: int = 0
    records_valid: int = 0
    records_partial: int = 0
    records_rejected: int = 0
    warnings_count: int = 0
    total_after_validation: int = 0
    unique_count: int = 0
    duplicate_count: int = 0
    output_path: str | None = None
    exported_count: int = 0

    def __post_init__(self) -> None:
        """Validate invariant consistency across pipeline stages."""
        expected_after_val = self.records_valid + self.records_partial
        if self.total_after_validation != expected_after_val:
            raise ValueError(
                f"Metric invariant violation: total_after_validation ({self.total_after_validation}) "
                f"must equal records_valid ({self.records_valid}) + records_partial ({self.records_partial})."
            )

        expected_dedup_total = self.unique_count + self.duplicate_count
        if self.total_after_validation != expected_dedup_total:
            raise ValueError(
                f"Metric invariant violation: total_after_validation ({self.total_after_validation}) "
                f"must equal unique_count ({self.unique_count}) + duplicate_count ({self.duplicate_count})."
            )

        if self.output_path is not None and self.exported_count != self.unique_count:
            raise ValueError(
                f"Metric invariant violation: exported_count ({self.exported_count}) "
                f"must equal unique_count ({self.unique_count}) when output_path is set."
            )

