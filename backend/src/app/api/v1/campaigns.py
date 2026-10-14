"""Campaign API endpoints according to API Contract Section 6.1, 6.2, and 6.3."""

from datetime import datetime
import logging
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import FileResponse

from app.core.constants import BACKEND_DIR, EXPORTS_DIR
from app.core.exceptions import (
    ExportFileMissingError,
    ExportNotReadyError,
    PathTraversalError,
    SourceUnapprovedError,
)
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
from app.schemas.common import StandardErrorResponse
from app.services.campaign_service import CampaignService

logger = logging.getLogger("app")
router = APIRouter(tags=["Campaigns"])


def resolve_export_file_path(export_file: str | None) -> Path | None:
    """
    Resolve export file path safely within EXPORTS_DIR.
    Returns Path if valid and safe, or raises PathTraversalError if outside EXPORTS_DIR.
    Returns None if export_file is None or empty.
    """
    if not export_file:
        return None

    exports_root = EXPORTS_DIR.resolve()
    file_path = Path(export_file)
    target_path = (BACKEND_DIR / file_path if not file_path.is_absolute() else file_path).resolve()

    if not target_path.is_relative_to(exports_root):
        raise PathTraversalError()

    return target_path


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
    responses={
        202: {"model": CreateCampaignResponse, "description": "Chiến dịch đã được tiếp nhận hợp lệ và đưa vào hàng đợi xử lý nền"},
        403: {"model": StandardErrorResponse, "description": "Chính sách từ chối (Chế độ LIVE chưa được phê duyệt)"},
        422: {"model": StandardErrorResponse, "description": "Dữ liệu cấu hình chiến dịch không hợp lệ"},
    },
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
    responses={
        200: {"model": CampaignDetailResponse, "description": "Thông tin chi tiết tiến độ, trạng thái và lỗi của chiến dịch"},
        404: {"model": StandardErrorResponse, "description": "Không tìm thấy chiến dịch yêu cầu"},
        422: {"model": StandardErrorResponse, "description": "Định dạng campaign_id không hợp lệ (yêu cầu UUID)"},
    },
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

    # Xác định tệp export có thực sự tồn tại và sẵn sàng trên đĩa hay không
    export_ready = False
    if campaign.status in {CampaignStatus.COMPLETED, CampaignStatus.PARTIAL_SUCCESS} and campaign.export_file:
        try:
            target_path = resolve_export_file_path(campaign.export_file)
            if target_path is not None and target_path.is_file():
                export_ready = True
        except PathTraversalError:
            export_ready = False

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
                raw_records_scanned=campaign.raw_records_scanned,
                records_extracted=campaign.records_extracted,
                valid_records=campaign.records_valid,
                partial_missing_records=campaign.records_partial,
                rejected_records=campaign.records_rejected,
                duplicates_removed=campaign.duplicates_removed,
                final_unique_leads=campaign.final_unique_leads,
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


@router.get(
    "/campaigns/{campaign_id}/export",
    summary="Tải tệp bảng tính Excel kết quả thu thập",
    response_class=FileResponse,
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
            "description": "Tải tệp Excel thành công",
        },
        403: {"model": StandardErrorResponse, "description": "Yêu cầu truy cập tệp bị từ chối (Path Traversal)"},
        404: {"model": StandardErrorResponse, "description": "Chiến dịch không tồn tại hoặc tệp Excel không tồn tại trên đĩa"},
        409: {"model": StandardErrorResponse, "description": "Chiến dịch chưa sẵn sàng để xuất tệp Excel"},
        422: {"model": StandardErrorResponse, "description": "Định dạng campaign_id không hợp lệ (yêu cầu UUID)"},
    },
)
async def export_campaign_leads(
    campaign_id: UUID,
    service: CampaignService = Depends(get_campaign_service),
) -> FileResponse:
    """
    Endpoint 3: Tải file Excel (.xlsx) chứa các bản ghi doanh nghiệp đã thu thập và xử lý.
    - Trả về HTTP 200 kèm FileResponse và header MIME type chuẩn.
    - Ném CampaignNotFoundError (HTTP 404) nếu không tìm thấy campaign.
    - Ném ExportNotReadyError (HTTP 409) nếu campaign chưa hoàn tất hoặc chưa có export_file.
    - Ném PathTraversalError (HTTP 403) nếu đường dẫn file bất thường hoặc ngoài EXPORTS_DIR.
    - Ném ExportFileMissingError (HTTP 404) nếu record báo có file nhưng file vật lý không tồn tại trên đĩa.
    """
    # 1. Tìm campaign; không tồn tại -> ném CampaignNotFoundError (HTTP 404)
    campaign = service.get_campaign(campaign_id)

    # 2. Kiểm tra trạng thái; nếu chưa COMPLETED hoặc PARTIAL_SUCCESS -> ném ExportNotReadyError (HTTP 409)
    if campaign.status not in {CampaignStatus.COMPLETED, CampaignStatus.PARTIAL_SUCCESS}:
        raise ExportNotReadyError(
            detail=f"Chiến dịch đang ở trạng thái {campaign.status.value}, tệp xuất chưa sẵn sàng."
        )

    # 3. Kiểm tra export_file đã có chưa
    if not campaign.export_file:
        raise ExportNotReadyError(detail="Chiến dịch chưa có thông tin tệp xuất dữ liệu.")

    # 4. Bảo vệ Path Traversal: xác thực đường dẫn lưu trữ nằm trong EXPORTS_DIR
    target_path = resolve_export_file_path(campaign.export_file)
    if target_path is None:
        raise ExportNotReadyError(detail="Đường dẫn tệp xuất không hợp lệ.")

    # 5. Xác minh file vật lý thực tế tồn tại trên đĩa
    if not target_path.is_file():
        logger.error(
            "Tệp Excel được đánh dấu sẵn sàng nhưng không tồn tại trên ổ đĩa: campaign_id=%s path=%s",
            campaign_id,
            target_path,
        )
        raise ExportFileMissingError(detail="Tệp Excel không tồn tại trên hệ thống lưu trữ máy chủ.")

    safe_download_filename = f"leads_{campaign_id}.xlsx"

    return FileResponse(
        path=str(target_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=safe_download_filename,
    )

