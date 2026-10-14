"""Campaign request, response, and detail schemas according to API Contract."""

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CreateCampaignRequest(BaseModel):
    """Payload for creating a new campaign via POST /api/v1/campaigns."""

    model_config = ConfigDict(extra="forbid")

    campaign_name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Tên chiến dịch thu thập (3–100 ký tự)",
    )
    industry: Literal["Education", "Manufacturing"] = Field(
        ...,
        description="Ngành mục tiêu: Education hoặc Manufacturing",
    )
    geographic_scope: Literal["NATIONWIDE", "PROVINCE"] = Field(
        ...,
        description="Phạm vi địa lý: NATIONWIDE hoặc PROVINCE",
    )
    target_province: str | None = Field(
        default=None,
        max_length=100,
        description="Mã hoặc tên tỉnh/thành phố khi scope là PROVINCE",
    )
    max_records: int = Field(
        default=20,
        ge=5,
        le=50,
        description="Số lượng bản ghi tối đa (5–50, mặc định 20)",
    )
    execution_mode: Literal["FIXTURE", "LIVE"] = Field(
        default="FIXTURE",
        description="Chế độ thực thi: FIXTURE hoặc LIVE",
    )

    @field_validator("campaign_name", mode="after")
    @classmethod
    def validate_campaign_name(cls, value: str) -> str:
        trimmed = value.strip()
        if len(trimmed) < 3:
            raise ValueError("Độ dài giá trị ngắn hơn mức tối thiểu yêu cầu (tối thiểu 3 ký tự).")
        # Check printable ASCII / unicode (no non-printable control characters)
        if any(ord(ch) < 32 and ch not in "\t\n\r" for ch in trimmed):
            raise ValueError("Tên chiến dịch không được chứa ký tự điều khiển.")
        return trimmed

    @field_validator("execution_mode", mode="before")
    @classmethod
    def normalize_execution_mode(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("target_province", mode="after")
    @classmethod
    def clean_target_province(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed if trimmed else None

    @model_validator(mode="after")
    def validate_geographic_rules(self) -> "CreateCampaignRequest":
        if self.geographic_scope == "PROVINCE":
            if not self.target_province:
                raise ValueError("Khi chọn phạm vi địa lý PROVINCE, trường target_province bắt buộc phải có giá trị.")
        elif self.geographic_scope == "NATIONWIDE":
            # For NATIONWIDE, target_province is set to None
            self.target_province = None
        return self


class CreateCampaignData(BaseModel):
    """Payload data in HTTP 202 Accepted response."""

    model_config = ConfigDict(extra="forbid")

    campaign_id: str
    campaign_name: str
    status: str = "PENDING"
    execution_mode: str = "FIXTURE"
    poll_interval_ms: int = 2000
    created_at: str
    message: str = "Chiến dịch đã được tiếp nhận hợp lệ và đưa vào hàng đợi xử lý nền."


class CreateCampaignResponse(BaseModel):
    """HTTP 202 response envelope for campaign creation."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    data: CreateCampaignData


class CampaignMetrics(BaseModel):
    """Mathematical metrics for campaign execution conforming to API Contract 4.3."""

    model_config = ConfigDict(extra="forbid")

    raw_records_scanned: int = 0
    records_extracted: int = 0
    valid_records: int = 0
    partial_missing_records: int = 0
    rejected_records: int = 0
    duplicates_removed: int = 0
    final_unique_leads: int = 0


class CampaignErrorItem(BaseModel):
    """Item detail in campaign errors list conforming to API Contract 4.4."""

    model_config = ConfigDict(extra="forbid")

    code: str
    stage: str
    message: str
    detail: str | None = None
    source_url: str | None = None
    timestamp: str
    recoverable: bool = True


class CampaignDetailData(BaseModel):
    """Full campaign detail payload conforming to API Contract 6.2."""

    model_config = ConfigDict(extra="forbid")

    campaign_id: str
    campaign_name: str
    status: str
    current_step: str = "STEP_INITIALIZATION"
    current_step_display: str = "Đang khởi tạo chiến dịch thu thập dữ liệu..."
    progress_percent: int = 0
    execution_mode: str = "FIXTURE"
    is_fixture_mode: bool = True
    metrics: CampaignMetrics = Field(default_factory=CampaignMetrics)
    errors: list[CampaignErrorItem] = Field(default_factory=list)
    total_records: int = 0
    warning_zero_records: bool = False
    export_file: str | None = None
    export_file_ready: bool = False
    export_url: str | None = None
    created_at: str
    updated_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


class CampaignDetailResponse(BaseModel):
    """HTTP 200 response envelope for campaign detail."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    data: CampaignDetailData
