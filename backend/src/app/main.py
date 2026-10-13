"""FastAPI application entry point, lifecycle configuration, and global error handlers."""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, List
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core import constants
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.schemas.common import ErrorDetail, StandardErrorResponse, ValidationErrorItem

logger = logging.getLogger("app")

# Patterns for field names that must never leak their input values in error responses
SENSITIVE_FIELD_PATTERNS = ("key", "secret", "password", "token", "cred", "auth", "pwd")


def get_iso_timestamp() -> str:
    """Format current UTC time to ISO 8601 string with trailing Z."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def is_sensitive_field(field_name: str) -> bool:
    """Check whether a field name corresponds to sensitive credentials or secrets."""
    field_lower = field_name.lower()
    return any(pattern in field_lower for pattern in SENSITIVE_FIELD_PATTERNS)


def sanitize_input_value(field_name: str, value: Any) -> Any:
    """
    Sanitize input values for error reports.
    Never exposes values for sensitive fields (API keys, passwords, tokens).
    Truncates non-sensitive strings to 50 chars and strips control characters.
    """
    if value is None or is_sensitive_field(field_name):
        return None

    val_str = str(value)
    # Remove non-printable control characters
    cleaned = "".join(ch for ch in val_str if ch.isprintable())
    if len(cleaned) > 50:
        return cleaned[:47] + "..."
    return cleaned


def translate_pydantic_error(err_type: str) -> str:
    """Provide clear Vietnamese validation error messages without framework leakage."""
    if err_type == "missing":
        return "Trường này là bắt buộc."
    if "too_short" in err_type:
        return "Độ dài giá trị ngắn hơn mức tối thiểu yêu cầu."
    if "too_long" in err_type:
        return "Độ dài giá trị vượt quá giới hạn tối đa cho phép."
    if "greater_than" in err_type or "less_than" in err_type:
        return "Giá trị nằm ngoài khoảng cho phép."
    if "int_parsing" in err_type or "int_type" in err_type:
        return "Giá trị phải là số nguyên hợp lệ."
    if "bool_parsing" in err_type:
        return "Giá trị phải là kiểu logic (true/false)."
    if "string_type" in err_type:
        return "Giá trị phải là chuỗi ký tự hợp lệ."
    if "list_type" in err_type:
        return "Giá trị phải là danh sách hợp lệ."
    if "dict_type" in err_type:
        return "Giá trị phải là đối tượng hợp lệ."
    if "enum" in err_type or "literal_error" in err_type:
        return "Giá trị không nằm trong danh mục được chấp nhận."
    if "extra_forbidden" in err_type:
        return "Trường dữ liệu này không được phép xuất hiện."
    if "json_invalid" in err_type:
        return "Dữ liệu JSON không hợp lệ."
    if "url" in err_type:
        return "Định dạng đường dẫn URL không hợp lệ."
    # Standard Vietnamese fallback instead of raw English framework message
    return "Dữ liệu trường không hợp lệ hoặc không đúng định dạng yêu cầu."


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    settings = get_settings()
    setup_logging(settings)
    app.state.start_time_monotonic = time.monotonic()
    app.state.active_campaigns_count = 0
    logger.info(
        "Application starting up: service=%s version=%s env=%s host=%s port=%d",
        constants.SERVICE_NAME,
        constants.APP_VERSION,
        settings.app_env,
        settings.app_host,
        settings.app_port,
    )
    yield
    logger.info("Application shutting down.")


def create_app() -> FastAPI:
    """Application factory for AI RPA Lead Collector Backend."""
    settings = get_settings()

    app = FastAPI(
        title="AI RPA Lead Collector Backend",
        version=constants.APP_VERSION,
        description="Backend API Modular Monolith cho hệ thống AI RPA Lead Collector",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api")

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic request validation errors (HTTP 422)."""
        validation_errors: List[ValidationErrorItem] = []
        for err in exc.errors():
            loc = err.get("loc", ())
            # Extract last field element if present
            field_name = str(loc[-1]) if loc else "body"
            err_type = err.get("type", "")
            translated_msg = translate_pydantic_error(err_type)
            input_val = sanitize_input_value(field_name, err.get("input"))

            validation_errors.append(
                ValidationErrorItem(
                    field=field_name,
                    message=translated_msg,
                    input_value=input_val,
                )
            )

        error_response = StandardErrorResponse(
            success=False,
            error=ErrorDetail(
                code=constants.ERR_CFG_INVALID,
                message="Dữ liệu gửi lên không đúng định dạng yêu cầu.",
                detail="Vui lòng kiểm tra lại các trường thông tin trong biểu mẫu.",
                stage=constants.STAGE_REQUEST_VALIDATION,
                timestamp=get_iso_timestamp(),
                path=request.url.path,
                validation_errors=validation_errors,
            ),
        )
        logger.info(
            "Request validation failed at path %s: errors_count=%d",
            request.url.path,
            len(validation_errors),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(),
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """
        Handle domain and application-specific exceptions.
        Guarantees exact business error codes (ERR_SRC_UNAPPROVED, ERR_PATH_TRAVERSAL,
        ERR_CAMPAIGN_NOT_FOUND, etc.) are never obscured by generic HTTP handlers.
        """
        if exc.status_code == status.HTTP_403_FORBIDDEN:
            logger.warning(
                "Security policy violation at path %s: code=%s message=%s",
                request.url.path,
                exc.code,
                exc.message,
            )
        elif exc.status_code >= 500:
            logger.error(
                "Application domain server error at path %s: code=%s status=%d",
                request.url.path,
                exc.code,
                exc.status_code,
            )
        else:
            logger.info(
                "Application domain exception at path %s: code=%s status=%d",
                request.url.path,
                exc.code,
                exc.status_code,
            )

        error_response = StandardErrorResponse(
            success=False,
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
                stage=exc.stage,
                timestamp=get_iso_timestamp(),
                path=request.url.path,
                validation_errors=exc.validation_errors,
            ),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Handle framework and route HTTP exceptions (400, 401, 403, 404, 405, 409, 429, 503).
        Provides sanitized, standardized public error messages without internal leaks.
        """
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            code = constants.ERR_ROUTE_NOT_FOUND
            message = "Đường dẫn yêu cầu không tồn tại."
            detail = "Vui lòng kiểm tra lại URL và phương thức HTTP của endpoint."
        elif exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            code = constants.ERR_METHOD_NOT_ALLOWED
            message = "Phương thức HTTP không được hỗ trợ."
            detail = "Endpoint này không hỗ trợ phương thức được yêu cầu. Vui lòng kiểm tra tài liệu API."
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = constants.ERR_FORBIDDEN
            message = "Truy cập bị từ chối."
            detail = "Bạn không có quyền thực hiện thao tác hoặc truy cập tài nguyên này."
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = constants.ERR_UNAUTHORIZED
            message = "Yêu cầu xác thực không thành công."
            detail = "Vui lòng cung cấp thông tin xác thực hợp lệ."
        elif exc.status_code == status.HTTP_400_BAD_REQUEST:
            code = constants.ERR_CFG_INVALID
            message = "Yêu cầu không hợp lệ."
            detail = "Cú pháp yêu cầu không đúng hoặc thiếu tham số cần thiết."
        elif exc.status_code == status.HTTP_409_CONFLICT:
            code = constants.ERR_CONFLICT
            message = "Xung đột trạng thái tài nguyên."
            detail = "Yêu cầu không thể hoàn thành do xung đột với trạng thái hiện tại của tài nguyên."
        elif exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            code = constants.ERR_RATE_LIMITED
            message = "Vượt quá giới hạn tần suất yêu cầu."
            detail = "Hệ thống đang tiếp nhận quá nhiều yêu cầu. Vui lòng thử lại sau giây lát."
        elif exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            code = constants.ERR_SERVICE_UNAVAILABLE
            message = "Dịch vụ tạm thời không khả dụng."
            detail = "Máy chủ đang bảo trì hoặc quá tải. Vui lòng thử lại sau."
        else:
            code = constants.ERR_SYS_INTERNAL
            message = "Lỗi xử lý yêu cầu HTTP."
            detail = "Hệ thống gặp sự cố khi xử lý yêu cầu mạng."

        logger.info(
            "HTTP exception at path %s: status=%d code=%s",
            request.url.path,
            exc.status_code,
            code,
        )

        error_response = StandardErrorResponse(
            success=False,
            error=ErrorDetail(
                code=code,
                message=message,
                detail=detail,
                stage=None,
                timestamp=get_iso_timestamp(),
                path=request.url.path,
                validation_errors=None,
            ),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Handle unhandled server exceptions (HTTP 500) without exposing stack traces or raw strings."""
        logger.exception(
            "Unhandled server exception [%s] at path: %s",
            exc.__class__.__name__,
            request.url.path,
        )

        error_response = StandardErrorResponse(
            success=False,
            error=ErrorDetail(
                code=constants.ERR_SYS_INTERNAL,
                message="Đã xảy ra sự cố nội bộ trên máy chủ.",
                detail="Hệ thống gặp lỗi không mong muốn. Chi tiết đã được ghi nhận trong file log máy chủ.",
                stage=None,
                timestamp=get_iso_timestamp(),
                path=request.url.path,
                validation_errors=None,
            ),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )

    return app


# Application instance for ASGI runners
app = create_app()


if __name__ == "__main__":
    import uvicorn

    server_settings = get_settings()
    uvicorn.run(
        "app.main:app",
        app_dir="src",
        host=server_settings.app_host,
        port=server_settings.app_port,
        reload=server_settings.debug,
    )
