"""Campaign business management service."""

from uuid import UUID

from app.core.exceptions import SourceUnapprovedError
from app.domain.campaigns.enums import CampaignStatus
from app.domain.campaigns.models import Campaign
from app.repositories.campaign_store import InMemoryCampaignStore


class CampaignService:
    """
    Service coordinates domain models and repositories to manage campaign lifecycle.

    Ghi chú về cơ chế đồng bộ hóa (Concurrency Note):
    - Các phương thức start_campaign() và finish_campaign() thực hiện quy trình:
      1. Đọc Campaign từ repository (nhận bản sao qua deepcopy()).
      2. Thay đổi trạng thái và áp dụng logic domain trên model.
      3. Ghi đè bản sao mới vào repository.
    - Với phạm vi MVP chạy đơn tiến trình, thiết kế này đơn giản và đủ tin cậy.
    - Khi triển khai đa worker hoặc xử lý Campaign đồng thời cao, cần bổ sung:
      cơ chế atomic state transitions ở tầng repository/database hoặc Optimistic Locking (versioning).
    """

    def __init__(self, store: InMemoryCampaignStore) -> None:
        self._store = store

    def create_campaign(
        self,
        *,
        campaign_name: str = "",
        execution_mode: str = "FIXTURE",
        max_records: int = 20,
        config: dict | None = None,
    ) -> Campaign:
        """
        Create a new Campaign in PENDING state.
        Normalizes execution_mode and in MVP rejects LIVE mode until sources are approved.
        """
        if not isinstance(execution_mode, str):
            raise ValueError("execution_mode phải là chuỗi")

        mode = execution_mode.strip().upper()

        if mode not in {"FIXTURE", "LIVE"}:
            raise ValueError("execution_mode phải là FIXTURE hoặc LIVE")

        # MVP: chưa cho chạy LIVE khi chưa tích hợp kiểm tra nguồn được phê duyệt.
        # Không tự động chuyển LIVE sang FIXTURE.
        if mode == "LIVE":
            raise SourceUnapprovedError()

        campaign = Campaign(
            campaign_name=campaign_name,
            execution_mode=mode,
            max_records=max_records,
            config=config if config is not None else {},
        )

        return self._store.create(campaign)

    def get_campaign(self, campaign_id: UUID) -> Campaign:
        """Retrieve a campaign by its UUID."""
        return self._store.get(campaign_id)

    def start_campaign(self, campaign_id: UUID) -> Campaign:
        """Transition a campaign from PENDING to RUNNING and persist update."""
        campaign = self._store.get(campaign_id)
        campaign.mark_running()
        return self._store.update(campaign)

    def finish_campaign(
        self,
        campaign_id: UUID,
        *,
        status: CampaignStatus,
        total_records: int = 0,
        error_count: int = 0,
        export_file: str | None = None,
        warning_zero_records: bool = False,
        error_code: str | None = None,
        error_message: str | None = None,
        raw_records_scanned: int = 0,
        records_extracted: int = 0,
        records_valid: int = 0,
        records_partial: int = 0,
        records_rejected: int = 0,
        duplicates_removed: int = 0,
        final_unique_leads: int = 0,
    ) -> Campaign:
        """Transition a campaign to a terminal state and persist update."""
        campaign = self._store.get(campaign_id)
        campaign.mark_finished(
            status,
            total_records=total_records,
            error_count=error_count,
            export_file=export_file,
            warning_zero_records=warning_zero_records,
            error_code=error_code,
            error_message=error_message,
        )
        campaign.raw_records_scanned = raw_records_scanned
        campaign.records_extracted = records_extracted
        campaign.records_valid = records_valid
        campaign.records_partial = records_partial
        campaign.records_rejected = records_rejected
        campaign.duplicates_removed = duplicates_removed
        campaign.final_unique_leads = final_unique_leads
        return self._store.update(campaign)


    def count_campaigns(self) -> int:
        """Return the total number of stored campaigns."""
        return self._store.count()

    def count_active_campaigns(self) -> int:
        """Return the number of campaigns that are still active (PENDING or RUNNING)."""
        return sum(
            campaign.status in {
                CampaignStatus.PENDING,
                CampaignStatus.RUNNING,
            }
            for campaign in self._store.list_all()
        )

