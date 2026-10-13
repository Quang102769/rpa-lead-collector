"""In-memory campaign store repository."""

from copy import deepcopy
from threading import RLock
from uuid import UUID

from app.core.exceptions import CampaignNotFoundError
from app.domain.campaigns.models import Campaign


class InMemoryCampaignStore:
    """
    Thread-safe in-memory store for Campaign domain models.

    Ghi chú về cơ chế đồng bộ hóa và giới hạn của RLock (Concurrency Note & Trade-offs):
    - RLock bảo vệ từng thao tác nguyên tử với dictionary trong RAM (create, get, update, count, clear),
      tránh race condition / memory corruption khi nhiều luồng truy cập cấu trúc dữ liệu đồng thời.
    - Giới hạn: RLock KHÔNG bảo vệ toàn bộ quy trình nghiệp vụ tổng hợp (đọc -> kiểm tra/sửa -> cập nhật).
      Nếu Request A và Request B cùng đọc 1 Campaign, Request A cập nhật xong, sau đó Request B cập nhật
      bản sao cũ, hiện tượng 'lost update' có thể xảy ra.
    - Với phạm vi MVP chạy đơn tiến trình (single-process), thiết kế này đơn giản và đủ tin cậy.
    - Khi mở rộng quy mô (nhiều worker / distributed / đồng thời cao), cần bổ sung:
        1. Cơ chế Optimistic Locking (ví dụ: trường version number trong Campaign model).
        2. Thao tác chuyển trạng thái nguyên tử có điều kiện (atomic compare-and-swap).
        3. Sử dụng Database với ACID transactions hoặc Distributed Lock (Redis Redlock).
    - Sử dụng deepcopy() ở cả đầu vào lẫn đầu ra để cô lập hoàn toàn tham chiếu, ngăn chặn
      việc thay đổi dữ liệu ngầm mà không qua phương thức update().
    """

    def __init__(self) -> None:
        self._campaigns: dict[UUID, Campaign] = {}
        self._lock = RLock()

    def create(self, campaign: Campaign) -> Campaign:
        """Store a new campaign in memory. Raises ValueError if id exists."""
        if not isinstance(campaign, Campaign):
            raise TypeError("campaign phải là một đối tượng Campaign")

        with self._lock:
            if campaign.campaign_id in self._campaigns:
                raise ValueError("campaign_id đã tồn tại")

            self._campaigns[campaign.campaign_id] = deepcopy(campaign)
            return deepcopy(campaign)

    def get(self, campaign_id: UUID) -> Campaign:
        """Retrieve a copy of a campaign by its UUID. Raises CampaignNotFoundError if missing."""
        if not isinstance(campaign_id, UUID):
            raise TypeError("campaign_id phải là một đối tượng UUID")

        with self._lock:
            campaign = self._campaigns.get(campaign_id)

            if campaign is None:
                raise CampaignNotFoundError()

            return deepcopy(campaign)

    def update(self, campaign: Campaign) -> Campaign:
        """Update an existing campaign. Raises CampaignNotFoundError if missing."""
        if not isinstance(campaign, Campaign):
            raise TypeError("campaign phải là một đối tượng Campaign")

        with self._lock:
            if campaign.campaign_id not in self._campaigns:
                raise CampaignNotFoundError()

            self._campaigns[campaign.campaign_id] = deepcopy(campaign)
            return deepcopy(campaign)

    def list_all(self) -> list[Campaign]:
        """Return deep copies of all campaigns in the store."""
        with self._lock:
            return [
                deepcopy(campaign)
                for campaign in self._campaigns.values()
            ]

    def count(self) -> int:
        """Return the count of campaigns stored in RAM."""
        with self._lock:
            return len(self._campaigns)

    def clear(self) -> None:
        """Clear all stored campaigns (used for testing or clean resets)."""
        with self._lock:
            self._campaigns.clear()
