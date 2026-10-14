"""Campaign domain models."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.core.exceptions import CampaignStateTransitionError
from app.domain.campaigns.enums import CampaignStatus

# Các trạng thái kết thúc (terminal states)
TERMINAL_STATUSES: set[CampaignStatus] = {
    CampaignStatus.COMPLETED,
    CampaignStatus.PARTIAL_SUCCESS,
    CampaignStatus.FAILED,
}

# Ma trận chuyển trạng thái thống nhất theo Tiêu chí 2.1
ALLOWED_TRANSITIONS: dict[CampaignStatus, set[CampaignStatus]] = {
    CampaignStatus.PENDING: {CampaignStatus.RUNNING, CampaignStatus.FAILED},
    CampaignStatus.RUNNING: {
        CampaignStatus.COMPLETED,
        CampaignStatus.PARTIAL_SUCCESS,
        CampaignStatus.FAILED,
    },
    CampaignStatus.COMPLETED: set(),
    CampaignStatus.PARTIAL_SUCCESS: set(),
    CampaignStatus.FAILED: set(),
}


def utc_now() -> datetime:
    """Lấy thời gian UTC có timezone."""
    return datetime.now(timezone.utc)


@dataclass
class Campaign:
    """Domain model lưu thông tin và trạng thái của một chiến dịch thu thập dữ liệu."""

    campaign_id: UUID = field(default_factory=uuid4)
    status: CampaignStatus = CampaignStatus.PENDING

    execution_mode: str = "FIXTURE"
    max_records: int = 20

    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    total_records: int = 0
    error_count: int = 0
    warning_zero_records: bool = False

    export_file: str | None = None
    error_code: str | None = None
    error_message: str | None = None

    # Có thể bổ sung cấu hình nghiệp vụ rõ kiểu ở bước tích hợp API.
    config: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.status, CampaignStatus):
            raise ValueError("status phải là CampaignStatus")

        if not isinstance(self.execution_mode, str):
            raise ValueError("execution_mode phải là chuỗi")

        self.execution_mode = self.execution_mode.upper()
        if self.execution_mode not in {"FIXTURE", "LIVE"}:
            raise ValueError("execution_mode phải là FIXTURE hoặc LIVE")

        # Type guard: bool là subclass của int trong Python nên cần type(x) is int
        if type(self.max_records) is not int:
            raise ValueError("max_records phải là số nguyên")

        if not 5 <= self.max_records <= 50:
            raise ValueError("max_records phải nằm trong khoảng 5–50")

        if type(self.total_records) is not int or self.total_records < 0:
            raise ValueError("total_records phải là số nguyên không âm")

        if type(self.error_count) is not int or self.error_count < 0:
            raise ValueError("error_count phải là số nguyên không âm")

        if not isinstance(self.warning_zero_records, bool):
            raise ValueError("warning_zero_records phải là kiểu boolean")

        # Xác thực tính nhất quán của timestamps với trạng thái
        if self.status == CampaignStatus.PENDING:
            if self.started_at is not None:
                raise ValueError("Campaign ở trạng thái PENDING không được có started_at")
            if self.completed_at is not None:
                raise ValueError("Campaign ở trạng thái PENDING không được có completed_at")
        elif self.status == CampaignStatus.RUNNING:
            if self.completed_at is not None:
                raise ValueError("Campaign ở trạng thái RUNNING không được có completed_at")

    @property
    def is_terminal(self) -> bool:
        """Kiểm tra xem chiến dịch đã đạt đến trạng thái kết thúc hay chưa."""
        return self.status in TERMINAL_STATUSES

    def can_transition_to(self, target_status: Any) -> bool:
        """Kiểm tra tính hợp lệ của việc chuyển sang target_status theo ma trận trạng thái."""
        if not isinstance(target_status, CampaignStatus):
            return False
        return target_status in ALLOWED_TRANSITIONS.get(self.status, set())

    def mark_running(self) -> None:
        """Chuyển trạng thái từ PENDING sang RUNNING khi bắt đầu xử lý."""
        if not self.can_transition_to(CampaignStatus.RUNNING):
            raise CampaignStateTransitionError(
                from_status=self.status.value,
                to_status=CampaignStatus.RUNNING.value,
            )

        now = utc_now()
        self.status = CampaignStatus.RUNNING
        self.started_at = now
        self.updated_at = now

    def mark_finished(
        self,
        status: CampaignStatus,
        *,
        total_records: int = 0,
        error_count: int = 0,
        export_file: str | None = None,
        warning_zero_records: bool = False,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Chuyển trạng thái sang một trong các trạng thái kết thúc hợp lệ:
        COMPLETED, PARTIAL_SUCCESS, hoặc FAILED.
        """
        if not isinstance(status, CampaignStatus):
            raise ValueError("status phải là CampaignStatus")

        if status not in TERMINAL_STATUSES:
            raise ValueError("mark_finished chỉ nhận trạng thái kết thúc")

        if not self.can_transition_to(status):
            raise CampaignStateTransitionError(
                from_status=self.status.value,
                to_status=status.value,
            )

        if type(total_records) is not int or total_records < 0:
            raise ValueError("total_records phải là số nguyên không âm")

        if type(error_count) is not int or error_count < 0:
            raise ValueError("error_count phải là số nguyên không âm")

        if not isinstance(warning_zero_records, bool):
            raise ValueError("warning_zero_records phải là kiểu boolean")

        now = utc_now()
        self.status = status
        self.total_records = total_records
        self.error_count = error_count
        self.export_file = export_file
        self.warning_zero_records = warning_zero_records
        self.error_code = error_code
        self.error_message = error_message
        self.completed_at = now
        self.updated_at = now

    def mark_failed(
        self,
        *,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Đánh dấu thất bại chuyên biệt khi có sự cố, hỗ trợ cả khi đang PENDING
        (lỗi hệ thống trước khi chạy) lẫn RUNNING (lỗi trong quá trình thu thập).
        Bảo toàn các thông tin bộ đếm hiện có.
        """
        if not self.can_transition_to(CampaignStatus.FAILED):
            raise CampaignStateTransitionError(
                from_status=self.status.value,
                to_status=CampaignStatus.FAILED.value,
            )

        now = utc_now()
        self.status = CampaignStatus.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.completed_at = now
        self.updated_at = now
