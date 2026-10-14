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
from uuid import UUID

from app.core import constants
from app.core.exceptions import CampaignNotFoundError
from app.domain.campaigns.enums import CampaignStatus
from app.services.campaign_service import CampaignService

logger = logging.getLogger("app")


def dispatch_campaign(
    campaign_id: UUID,
    service: CampaignService | None = None,
) -> None:
    """
    Asynchronously orchestrate background execution of a campaign.

    1. Nhận campaign_id và service (nếu service=None, tự động lấy từ container/app state).
    2. Độc lập hoàn toàn với tầng router HTTP.
    3. Gọi CampaignService.start_campaign() để chuyển trạng thái từ PENDING sang RUNNING.
    4. Ghi log có cấu trúc tại thời điểm bắt đầu và khi chuyển trạng thái thành công.
    5. Kiểm soát toàn diện ngoại lệ:
       - Nếu không tìm thấy Campaign (CampaignNotFoundError): ghi log cảnh báo rõ ràng.
       - Nếu có lỗi bất ngờ khác: chuyển trạng thái sang FAILED kèm mã lỗi ERR_SYS_INTERNAL,
         tuyệt đối không để lỗi bị nuốt im lặng hay treo trạng thái.
    6. Giữ nguyên trạng thái RUNNING làm stub cho Task 4 Pipeline.
    """
    if service is None:
        try:
            from app.main import app

            service = getattr(app.state, "campaign_service", None)
            if service is None:
                store = getattr(app.state, "campaign_store", None)
                if store is not None:
                    service = CampaignService(store=store)
        except Exception as exc:
            logger.error("Không thể lấy CampaignService từ container ứng dụng: %s", exc)

    if service is None:
        logger.error(
            "dispatch_campaign thất bại: Không tìm thấy CampaignService cho campaign_id=%s",
            campaign_id,
        )
        return

    logger.info("Bắt đầu xử lý nền cho chiến dịch: campaign_id=%s", campaign_id)
    try:
        service.start_campaign(campaign_id)
        logger.info(
            "Chiến dịch đã chuyển sang trạng thái RUNNING: campaign_id=%s",
            campaign_id,
        )
    except CampaignNotFoundError:
        logger.error(
            "dispatch_campaign thất bại: Không tìm thấy campaign_id=%s trong store để xử lý nền.",
            campaign_id,
        )
    except Exception as exc:
        logger.exception(
            "Lỗi nghiêm trọng khi điều phối chiến dịch nền: campaign_id=%s error=%s",
            campaign_id,
            exc,
        )
        try:
            service.finish_campaign(
                campaign_id,
                status=CampaignStatus.FAILED,
                error_code=constants.ERR_SYS_INTERNAL,
                error_message="Lỗi hệ thống khi khởi chạy tiến trình xử lý nền.",
            )
        except Exception:
            logger.exception(
                "Không thể cập nhật trạng thái FAILED cho campaign_id=%s",
                campaign_id,
            )

