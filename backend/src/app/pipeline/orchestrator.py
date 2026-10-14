"""Pipeline orchestrator for the RPA Lead Collector MVP."""

import logging
from pathlib import Path
from typing import Any, Callable, TypeVar

from app.collectors.fixture_collector import FixtureCollector
from app.core.exceptions import ConfigError
from app.deduplication.deduplicator import Deduplicator
from app.exporters.excel_exporter import ExcelExporter
from app.normalization.geo_normalizer import GeoNormalizer
from app.pipeline.models import PipelineResult
from app.validation.lead_validator import LeadValidator

logger = logging.getLogger(__name__)

T = TypeVar("T")



class PipelineOrchestrator:
    """Coordinate the lead processing pipeline."""

    def __init__(
        self,
        collector: FixtureCollector | None = None,
        validator: LeadValidator | None = None,
        geo_normalizer: GeoNormalizer | None = None,
        deduplicator: Deduplicator | None = None,
        exporter: ExcelExporter | None = None,
    ) -> None:
        self.collector = (
            collector if collector is not None else FixtureCollector()
        )
        self.validator = (
            validator if validator is not None else LeadValidator()
        )
        self.geo_normalizer = (
            geo_normalizer
            if geo_normalizer is not None
            else GeoNormalizer()
        )
        self.deduplicator = (
            deduplicator if deduplicator is not None else Deduplicator()
        )
        self.exporter = (
            exporter if exporter is not None else ExcelExporter()
        )

    @staticmethod
    def _check_invariant(condition: bool, stage: str, message: str) -> None:
        """Validate a pipeline invariant and log the failing stage."""
        if not condition:
            logger.error(
                "Pipeline invariant violation: stage=%s, detail=%s",
                stage,
                message,
            )
            raise RuntimeError(
                f"Pipeline invariant violation at stage '{stage}': {message}"
            )

    @staticmethod
    def _execute_stage(stage: str, operation: Callable[[], T]) -> T:
        """Execute a stage, log its failure, and preserve the exception."""
        logger.info("Pipeline stage started: %s", stage)

        try:
            result = operation()
        except Exception:
            logger.exception("Pipeline stage failed: %s", stage)
            raise

        logger.info("Pipeline stage completed: %s", stage)
        return result

    def run(
        self,
        config: dict[str, Any],
        output_path: str | Path,
        *,
        execution_mode: str = "FIXTURE",
        allowed_domains: list[str] | None = None,
        overwrite: bool = False,
    ) -> PipelineResult:
        """Run collection, validation, normalization, deduplication and export."""
        # Validate industry presence in campaign config
        industry = config.get("industry") if isinstance(config, dict) else None
        if not industry or not isinstance(industry, str) or not industry.strip():
            raise ConfigError(
                message="Dữ liệu cấu hình chiến dịch không hợp lệ.",
                detail="Cấu hình chiến dịch thiếu trường bắt buộc 'industry' kiểu chuỗi.",
            )
        expected_industry = industry.strip()

        # 1. Collect raw leads.
        raw_leads = self._execute_stage(
            "collector",
            lambda: self.collector.collect(config),
        )
        total_collected = len(raw_leads)

        # 2. Validate records. VALID and PARTIAL records may continue.
        validation_result = self._execute_stage(
            "validator",
            lambda: self.validator.validate_batch(
                leads=raw_leads,
                expected_industry=expected_industry,
                execution_mode=execution_mode,
                allowed_domains=allowed_domains,
            ),
        )

        valid_leads = validation_result.valid_records
        total_after_validation = len(valid_leads)

        self._check_invariant(
            validation_result.warnings_count >= 0,
            "validator",
            "warnings_count must not be negative",
        )
        self._check_invariant(
            validation_result.records_valid >= 0
            and validation_result.records_partial >= 0
            and validation_result.records_rejected >= 0,
            "validator",
            "validation metric counts must not be negative",
        )
        self._check_invariant(
            len(valid_leads)
            == validation_result.records_valid + validation_result.records_partial,
            "validator",
            "valid_records count does not match validation metrics",
        )
        self._check_invariant(
            total_collected
            == (
                validation_result.records_valid
                + validation_result.records_partial
                + validation_result.records_rejected
            ),
            "validator",
            "collected count does not equal valid + partial + rejected",
        )

        # 3. Normalize geography without dropping records.
        normalized_leads = self._execute_stage(
            "geo_normalizer",
            lambda: self.geo_normalizer.normalize_batch(valid_leads),
        )

        self._check_invariant(
            len(normalized_leads) == total_after_validation,
            "geo_normalizer",
            (
                f"expected {total_after_validation} records, "
                f"received {len(normalized_leads)}"
            ),
        )

        # 4. Deduplicate normalized records.
        dedup_result = self._execute_stage(
            "deduplicator",
            lambda: self.deduplicator.deduplicate(normalized_leads),
        )

        self._check_invariant(
            dedup_result.unique_count >= 0 and dedup_result.duplicate_count >= 0,
            "deduplicator",
            "deduplication counts must not be negative",
        )
        self._check_invariant(
            dedup_result.total_processed == total_after_validation,
            "deduplicator",
            (
                f"expected {total_after_validation} processed records, "
                f"received {dedup_result.total_processed}"
            ),
        )
        self._check_invariant(
            dedup_result.unique_count == len(dedup_result.unique_records),
            "deduplicator",
            "unique_count does not match unique_records length",
        )
        self._check_invariant(
            dedup_result.total_processed
            == dedup_result.unique_count + dedup_result.duplicate_count,
            "deduplicator",
            "processed count does not equal unique + duplicate",
        )


        # 5. Export unique records. Empty input is allowed.
        exported_path = self._execute_stage(
            "exporter",
            lambda: self.exporter.export(
                records=dedup_result.unique_records,
                output_path=output_path,
                overwrite=overwrite,
            ),
        )

        # Build the success result only after export has succeeded.
        result = PipelineResult(
            total_collected=total_collected,
            records_valid=validation_result.records_valid,
            records_partial=validation_result.records_partial,
            records_rejected=validation_result.records_rejected,
            warnings_count=validation_result.warnings_count,
            total_after_validation=total_after_validation,
            unique_count=dedup_result.unique_count,
            duplicate_count=dedup_result.duplicate_count,
            output_path=exported_path,
            exported_count=dedup_result.unique_count,
        )

        logger.info(
            "Pipeline completed: collected=%d, accepted=%d, "
            "rejected=%d, unique=%d, duplicates=%d, exported=%d, "
            "output=%s",
            result.total_collected,
            result.total_after_validation,
            result.records_rejected,
            result.unique_count,
            result.duplicate_count,
            result.exported_count,
            result.output_path,
        )

        return result
