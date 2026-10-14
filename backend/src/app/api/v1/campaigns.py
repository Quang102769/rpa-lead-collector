"""Campaign API endpoints according to API Contract Section 6.1 and 6.2."""

from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.core.exceptions import SourceUnapprovedError
from app.dependencies import get_campaign_service
from app.domain.campaigns.enums import CampaignStatus
from app.pipeline.dispatcher import dispatch_campaign
from app.schemas.campaign import (
    CampaignDetailData,
    CampaignDetailResponse,
    CampaignErrorItem,
    CampaignMetrics,
    CreateCampaignData,
    CreateCampaignResponse,
    CreateCampaignRequest,
)
from app.services.campaign_service import CampaignService

router = APIRouter(tags=["Campaigns"])


def format_iso_z(dt: datetime | None) -> str | None:
    """Format datetime to ISO 8601 UTC with trailing Z."""
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


@router.post(
    "/campaigns",
    response_model=CreateCampaignResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Khởi tạo chiến dịch thu thập mới",
)
async def create_campaign(
    payload: CreateCampaignRequest,
    background_tasks: BackgroundTasks,
    service: CampaignService = Depends(get_campaign_service),
) -> CreateCampaignResponse:
    """
    Endpoint 1: Khởi tạo chiến dịch thu thập mới.
    - Kiểm tra chính sách LIVE mode đồng bộ: ném HTTP 403 nếu chưa duyệt.
    - Lưu Campaign ở trạng thái PENDING.
    - Đăng ký BackgroundTasks gọi dispatch_campaign.
    - Trả về ngay lập tức HTTP 202 Accepted.
    """
    if payload.execution_mode == "LIVE":
        raise SourceUnapprovedError()

    campaign = service.create_campaign(
        campaign_name=payload.campaign_name,
        execution_mode=payload.execution_mode,
        max_records=payload.max_records,
        config={
            "industry": payload.industry,
            "geographic_scope": payload.geographic_scope,
            "target_province": payload.target_province,
        },
    )

    # Đăng ký background task chạy sau khi HTTP response 202 được gửi
    background_tasks.add_task(dispatch_campaign, campaign.campaign_id, service)

    return CreateCampaignResponse(
        success=True,
        data=CreateCampaignData(
            campaign_id=str(campaign.campaign_id),
            campaign_name=campaign.campaign_name,
            status=campaign.status.value,
            execution_mode=campaign.execution_mode,
            poll_interval_ms=2000,
            created_at=format_iso_z(campaign.created_at) or "",
            message="Chiến dịch đã được tiếp nhận hợp lệ và đưa vào hàng đợi xử lý nền.",
        ),
    )


@router.get(
    "/campaigns/{campaign_id}",
    response_model=CampaignDetailResponse,
    summary="Thăm dò trạng thái, tiến độ và báo lỗi pipeline",
)
async def get_campaign(
    campaign_id: UUID,
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignDetailResponse:
    """
    Endpoint 2: Thăm dò trạng thái, tiến độ và lỗi của chiến dịch.
    - Trả về HTTP 200 kèm tiến độ, chỉ số metrics và mảng lỗi.
    - Ném CampaignNotFoundError (HTTP 404) nếu không tìm thấy.
    """
    campaign = service.get_campaign(campaign_id)

    # Xác định tiến độ phần trăm và bước hiện tại
    if campaign.status == CampaignStatus.PENDING:
        progress_percent = 0
        current_step = "STEP_INITIALIZATION"
        current_step_display = "Chiến dịch đang trong hàng đợi xử lý nền..."
    elif campaign.status == CampaignStatus.RUNNING:
        progress_percent = 10
        current_step = "STEP_POLICY_CHECK"
        current_step_display = "Đang kiểm tra chính sách nguồn và khởi tạo tiến trình thu thập..."
    elif campaign.status == CampaignStatus.COMPLETED:
        progress_percent = 100
        current_step = "STEP_COMPLETED"
        current_step_display = "Chiến dịch hoàn tất thành công. Tệp Excel đã sẵn sàng để tải về."
    elif campaign.status == CampaignStatus.PARTIAL_SUCCESS:
        progress_percent = 100
        current_step = "STEP_EXPORT_COMPLETED"
        current_step_display = "Đã xuất bảng tính Excel thành công (Có cảnh báo lỗi một phần)."
    else:  # FAILED
        progress_percent = 10
        current_step = "STEP_FAILED"
        current_step_display = campaign.error_message or "Chiến dịch gặp sự cố và đã dừng lại."

    errors: list[CampaignErrorItem] = []
    if campaign.error_code:
        errors.append(
            CampaignErrorItem(
                code=campaign.error_code,
                stage="STAGE_REQUEST_VALIDATION" if campaign.status == CampaignStatus.PENDING else "STAGE_POLICY_CHECK",
                message=campaign.error_message or "Lỗi xử lý chiến dịch",
                detail=None,
                source_url=None,
                timestamp=format_iso_z(campaign.updated_at) or "",
                recoverable=False,
            )
        )

    export_ready = bool(
        campaign.export_file
        and campaign.status in {CampaignStatus.COMPLETED, CampaignStatus.PARTIAL_SUCCESS}
    )
    export_url = f"/api/v1/campaigns/{campaign.campaign_id}/export" if export_ready else None

    return CampaignDetailResponse(
        success=True,
        data=CampaignDetailData(
            campaign_id=str(campaign.campaign_id),
            campaign_name=campaign.campaign_name,
            status=campaign.status.value,
            current_step=current_step,
            current_step_display=current_step_display,
            progress_percent=progress_percent,
            execution_mode=campaign.execution_mode,
            is_fixture_mode=(campaign.execution_mode == "FIXTURE"),
            metrics=CampaignMetrics(
                raw_records_scanned=0,
                records_extracted=0,
                valid_records=0,
                partial_missing_records=0,
                rejected_records=0,
                duplicates_removed=0,
                final_unique_leads=campaign.total_records,
            ),
            errors=errors,
            total_records=campaign.total_records,
            warning_zero_records=campaign.warning_zero_records,
            export_file=campaign.export_file,
            export_file_ready=export_ready,
            export_url=export_url,
            created_at=format_iso_z(campaign.created_at) or "",
            updated_at=format_iso_z(campaign.updated_at),
            started_at=format_iso_z(campaign.started_at),
            completed_at=format_iso_z(campaign.completed_at),
        ),
    )
