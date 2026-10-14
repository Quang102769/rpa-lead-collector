
"""Application exception hierarchy."""

from typing import Any

from app.core import constants


class AppException(Exception):
    """Base exception for domain and application errors."""

    def __init__(
        self,
        code: str,
        message: str,
        detail: str | None = None,
        status_code: int = 400,
        stage: str | None = None,
        validation_errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail
        self.status_code = status_code
        self.stage = stage
        self.validation_errors = validation_errors


class ConfigError(AppException):
    """Invalid campaign configuration or request data."""

    def __init__(
        self,
        message: str = "Dữ liệu cấu hình chiến dịch không hợp lệ.",
        detail: str | None = None,
        validation_errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            code=constants.ERR_CFG_INVALID,
            message=message,
            detail=detail,
            status_code=422,
            stage=constants.STAGE_REQUEST_VALIDATION,
            validation_errors=validation_errors,
        )


class CampaignNotFoundError(AppException):
    """Raised when a campaign does not exist."""

    def __init__(
        self,
        message: str = "Không tìm thấy chiến dịch yêu cầu.",
        detail: str | None = "Kiểm tra campaign_id và thử lại.",
    ) -> None:
        super().__init__(
            code=constants.ERR_CAMPAIGN_NOT_FOUND,
            message=message,
            detail=detail,
            status_code=404,
        )


# Backward-compatible alias
ResourceNotFoundError = CampaignNotFoundError


class CampaignStateTransitionError(AppException, ValueError):
    """Raised when an invalid campaign status transition is attempted."""

    def __init__(
        self,
        from_status: str,
        to_status: str,
        message: str | None = None,
    ) -> None:
        msg = message or f"Không thể chuyển {from_status} sang {to_status}"
        super().__init__(
            code=constants.ERR_CONFLICT,
            message=msg,
            detail="Trạng thái hiện tại không cho phép thao tác chuyển đổi này.",
            status_code=400,
            stage=constants.STAGE_POLICY_CHECK,
        )


class ExportNotReadyError(AppException):
    """Raised when the export is not ready."""

    def __init__(
        self,
        message: str = "Tệp Excel chưa sẵn sàng.",
        detail: str | None = None,
    ) -> None:
        super().__init__(
            code=constants.ERR_EXPORT_NOT_READY,
            message=message,
            detail=detail,
            status_code=400,
            stage=constants.STAGE_EXPORT,
        )


class ExportFileMissingError(AppException):
    """Raised when an expected export file is missing."""

    def __init__(
        self,
        message: str = "Không tìm thấy tệp Excel.",
        detail: str | None = None,
    ) -> None:
        super().__init__(
            code=constants.ERR_EXPORT_FILE_MISSING,
            message=message,
            detail=detail,
            status_code=404,
            stage=constants.STAGE_EXPORT,
        )


class PathTraversalError(AppException):
    """Raised when an unsafe file path is detected."""

    def __init__(
        self,
        message: str = "Yêu cầu truy cập tệp bị từ chối.",
        detail: str | None = (
            "Đường dẫn nằm ngoài thư mục lưu trữ được phép."
        ),
    ) -> None:
        super().__init__(
            code=constants.ERR_PATH_TRAVERSAL,
            message=message,
            detail=detail,
            status_code=403,
            stage=constants.STAGE_EXPORT,
        )


class SourceUnapprovedError(AppException):
    """Raised when a LIVE source is not approved."""

    def __init__(
        self,
        message: str = "Nguồn dữ liệu trực tiếp chưa được phê duyệt chính thức.",
        detail: str | None = (
            "Nguồn thu thập LIVE chưa có văn bản phê duyệt từ TechLead (DEC-01). "
            "Vui lòng chọn execution_mode là FIXTURE."
        ),
    ) -> None:
        super().__init__(
            code=constants.ERR_SRC_UNAPPROVED,
            message=message,
            detail=detail,
            status_code=403,
            stage=constants.STAGE_REQUEST_VALIDATION,
        )


class InternalServerError(AppException):
    """Raised for an internal server failure."""

    def __init__(self) -> None:
        super().__init__(
            code=constants.ERR_SYS_INTERNAL,
            message="Đã xảy ra sự cố nội bộ trên máy chủ.",
            detail="Vui lòng thử lại sau. Nếu lỗi tiếp diễn, hãy liên hệ quản trị viên.",
            status_code=500,
        )