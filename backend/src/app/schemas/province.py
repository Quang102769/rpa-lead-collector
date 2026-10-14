"""Province schemas conforming to API Contract Section 6.5."""

from pydantic import BaseModel, ConfigDict, Field


class ProvinceItem(BaseModel):
    """Details for a single administrative province unit."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., description="Mã đơn vị hành chính cấp tỉnh (2 chữ số)")
    name: str = Field(..., description="Tên chính thức của tỉnh/thành phố")
    type: str = Field(default="tinh", description="Loại đơn vị: thanh_pho hoặc tinh")
    region: str | None = Field(default=None, description="Vùng miền (Miền Bắc, Miền Trung, Miền Nam, Tây Nguyên)")
    is_active: bool = Field(default=True, description="Trạng thái hiệu lực hiện hành")
    aliases: list[str] = Field(default_factory=list, description="Các tên gọi tương đương, viết tắt")


class ProvinceListData(BaseModel):
    """Payload data for provinces reference."""

    model_config = ConfigDict(extra="forbid")

    version: str
    source_reference: str
    last_updated: str
    total_count: int
    default_selection: str = "48"
    provinces: list[ProvinceItem]


class ProvinceListResponse(BaseModel):
    """HTTP 200 response envelope for provinces reference list."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    data: ProvinceListData
