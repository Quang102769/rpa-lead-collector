"""
Background task dispatcher for campaign execution.

Ghi chú về cơ chế xử lý nền (Concurrency & Durability Note):
- FastAPI.BackgroundTasks chạy hoàn toàn in-process trong cùng tiến trình máy chủ,
  thực thi bất đồng bộ trên event loop sau khi HTTP response đã được trả về cho client.
- Giới hạn độ bền vững (Not a durable queue): Đây KHÔNG PHẢI là hàng đợi bền vững
  (durable message broker). Nếu tiến trình máy chủ bị dừng, khởi động lại hoặc gặp sự cố crash,
  các tác vụ đang chạy hoặc đang chờ trong BackgroundTasks sẽ bị gián đoạn và mất trạng thái trong RAM.
- Trong Phase 1, kiến trúc Modular Monolith chạy in-process đáp ứng hoàn hảo môi trường Local PoC/Demo.
- Trong Phase 4, cơ chế này sẽ được thay thế bằng Distributed Task Queue (Redis/Celery/ARQ)
  với các Worker chạy ở tiến trình độc lập, hỗ trợ persistence và retry tự động.
"""

import logging
from pathlib import Path
from uuid import UUID

from app.core import constants
from app.core.exceptions import CampaignNotFoundError
from app.domain.campaigns.enums import CampaignStatus
from app.pipeline.orchestrator import PipelineOrchestrator
from app.services.campaign_service import CampaignService

logger = logging.getLogger("app")


def dispatch_campaign(
    campaign_id: UUID,
    service: CampaignService | None = None,
    orchestrator: PipelineOrchestrator | None = None,
) -> None:
    """Execute a campaign and persist its terminal status."""

    # 1. Resolve CampaignService from the application when not injected.
    if service is None:
        try:
            from app.main import app

            service = getattr(app.state, "campaign_service", None)
            if service is None:
                store = getattr(app.state, "campaign_store", None)
                if store is not None:
                    service = CampaignService(store=store)
        except Exception:
            logger.exception(
                "Cannot resolve CampaignService: campaign_id=%s",
                campaign_id,
            )

    if service is None:
        logger.error(
            "CampaignService unavailable: campaign_id=%s",
            campaign_id,
        )
        return

    pipeline = (
        orchestrator
        if orchestrator is not None
        else PipelineOrchestrator()
    )

    # 2. Load the campaign and guard its state before starting.
    try:
        campaign = service.get_campaign(campaign_id)
    except CampaignNotFoundError:
        logger.error(
            "Không tìm thấy campaign_id=%s trong store để xử lý nền.",
            campaign_id,
        )
        return
    except Exception:
        logger.exception(
            "Không thể lấy campaign_id=%s để xử lý nền.",
            campaign_id,
        )
        return

    # Do not overwrite terminal states or start a campaign twice.
    if campaign.is_terminal:
        logger.warning(
            "Campaign đã kết thúc, bỏ qua dispatch: campaign_id=%s status=%s",
            campaign_id,
            campaign.status.value,
        )
        return

    try:
        service.start_campaign(campaign_id)
    except CampaignNotFoundError:
        logger.error(
            "Không tìm thấy campaign_id=%s khi bắt đầu xử lý nền.",
            campaign_id,
        )
        return
    except Exception:
        logger.exception(
            "Không thể khởi động campaign_id=%s.",
            campaign_id,
        )
        try:
            service.finish_campaign(
                campaign_id,
                status=CampaignStatus.FAILED,
                error_code=constants.ERR_SYS_INTERNAL,
                error_message="Lỗi hệ thống khi khởi động chiến dịch.",
            )
        except Exception:
            logger.exception(
                "Không thể đánh dấu FAILED sau lỗi khởi động: campaign_id=%s",
                campaign_id,
            )
        return

    logger.info(
        "Campaign started: campaign_id=%s mode=%s",
        campaign_id,
        campaign.execution_mode,
    )

    # 3. Build the pipeline configuration from the saved campaign.
    pipeline_config = dict(campaign.config)
    pipeline_config.setdefault("max_records", campaign.max_records)

    # Phase 1 output location. The exporter creates parent directories.
    output_path = Path("exports") / f"campaign_{campaign_id}.xlsx"

    # 4. Execute the pipeline. Do not mark the campaign successful on error.
    try:
        result = pipeline.run(
            config=pipeline_config,
            output_path=output_path,
            execution_mode=campaign.execution_mode,
            allowed_domains=pipeline_config.get("allowed_domains"),
        )
    except Exception as exc:
        logger.exception(
            "Campaign pipeline failed: campaign_id=%s",
            campaign_id,
        )

        try:
            service.finish_campaign(
                campaign_id,
                status=CampaignStatus.FAILED,
                error_code=constants.ERR_SYS_INTERNAL,
                error_message=(
                    f"Pipeline execution failed: {type(exc).__name__}"
                ),
            )
        except Exception:
            logger.exception(
                "Cannot persist FAILED status: campaign_id=%s",
                campaign_id,
            )
        return

    # 5. Persist success only after the export has succeeded.
    try:
        service.finish_campaign(
            campaign_id,
            status=CampaignStatus.COMPLETED,
            total_records=result.exported_count,
            error_count=result.records_rejected,
            export_file=result.output_path,
            warning_zero_records=(result.exported_count == 0),
            raw_records_scanned=result.total_collected,
            records_extracted=result.total_collected,
            records_valid=result.records_valid,
            records_partial=result.records_partial,
            records_rejected=result.records_rejected,
            duplicates_removed=result.duplicate_count,
            final_unique_leads=result.unique_count,
        )

    except Exception:
        logger.exception(
            "Pipeline succeeded but campaign completion could not be persisted: "
            "campaign_id=%s",
            campaign_id,
        )
        return

    logger.info(
        "Campaign completed: campaign_id=%s collected=%d exported=%d "
        "rejected=%d duplicates=%d output=%s",
        campaign_id,
        result.total_collected,
        result.exported_count,
        result.records_rejected,
        result.duplicate_count,
        result.output_path,
    )
