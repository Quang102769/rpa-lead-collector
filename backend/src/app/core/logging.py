"""Logging configuration with secret redaction filter and campaign audit logger."""

import logging
from pathlib import Path
import re
import sys
import traceback

from app.core import constants
from app.core.config import Settings, get_settings


class LogRedactionFilter(logging.Filter):
    """
    Log filter that redacts sensitive values such as API keys, tokens,
    and passwords from all log records, including exception tracebacks.
    """

    REDACTED_STR: str = "***REDACTED***"

    # Specific patterns for Authorization headers, Bearer tokens, and credential fields
    PATTERNS = [
        # Pattern 1: Authorization: Bearer <token> or Authorization: <token>
        re.compile(r"((?:authorization|auth)\s*[:=]\s*(?:bearer\s+)?)[^\s,;'\"]+", re.IGNORECASE),
        # Pattern 2: Bearer <token>
        re.compile(r"(bearer\s+)[^\s,;'\"]+", re.IGNORECASE),
        # Pattern 3: api_key, secret, password, auth_token, access_token, token
        re.compile(r"(['\"]?(?:(?:api[_-]?)?key|(?:client[_-]?)?secret|password|(?:access[_-]|auth[_-])?token)['\"]?\s*[:=]\s*['\"]?)[^\s,;'\"]+", re.IGNORECASE),
        # Pattern 4: Credit card numbers (16 digits grouped or continuous)
        re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
    ]

    def __init__(self, known_secret: str | None = None) -> None:
        super().__init__()
        self.known_secret = known_secret

    def filter(self, record: logging.LogRecord) -> bool:
        # 1. Format and redact main log message
        try:
            formatted_msg = record.getMessage()
            record.msg = self.redact(formatted_msg)
            record.args = ()
        except Exception:
            if isinstance(record.msg, str):
                record.msg = self.redact(record.msg)

        # 2. Pre-render and redact exception tracebacks if present
        if record.exc_info:
            try:
                tb_str = "".join(traceback.format_exception(*record.exc_info))
                record.exc_text = self.redact(tb_str)
            except Exception:
                pass

        # 3. Redact stack info if present
        if record.stack_info:
            try:
                record.stack_info = self.redact(record.stack_info)
            except Exception:
                pass

        return True

    def redact(self, text: str) -> str:
        # 1. Redact known secret if provided and long enough
        if self.known_secret and len(self.known_secret) > 3 and self.known_secret in text:
            text = text.replace(self.known_secret, self.REDACTED_STR)

        # 2. Redact regex patterns
        for pattern in self.PATTERNS:
            if pattern.groups > 0:
                text = pattern.sub(r"\1" + self.REDACTED_STR, text)
            else:
                text = pattern.sub(self.REDACTED_STR, text)

        return text


def setup_logging(settings: Settings | None = None) -> logging.Logger:
    """Initialize structured logging with redaction filter for root and framework loggers."""
    # Ensure logs directory exists
    constants.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    log_level = logging.DEBUG if (settings and settings.debug) else logging.INFO
    root_logger.setLevel(log_level)

    # Standard console format
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Avoid duplicate handlers if already initialized
    if not root_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    else:
        for handler in root_logger.handlers:
            handler.setLevel(log_level)

    known_secret = settings.llm_api_key if settings else None
    redaction_filter = LogRedactionFilter(known_secret=known_secret)

    # Attach filter to root logger
    root_logger.filters = [f for f in root_logger.filters if not isinstance(f, LogRedactionFilter)]
    root_logger.addFilter(redaction_filter)

    # Attach filter to all existing handlers on root logger
    for handler in root_logger.handlers:
        handler.filters = [f for f in handler.filters if not isinstance(f, LogRedactionFilter)]
        handler.addFilter(redaction_filter)

    # Attach filter to Uvicorn and FastAPI loggers to prevent leaking in framework/access logs
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        target_logger = logging.getLogger(logger_name)
        target_logger.filters = [f for f in target_logger.filters if not isinstance(f, LogRedactionFilter)]
        target_logger.addFilter(redaction_filter)
        for h in target_logger.handlers:
            h.filters = [f for f in h.filters if not isinstance(f, LogRedactionFilter)]
            h.addFilter(redaction_filter)

    return logging.getLogger("app")


def get_campaign_logger(campaign_id: str, settings: Settings | None = None) -> logging.Logger:
    """
    Get or configure a dedicated file logger for a specific campaign run according to
    architecture.md Section 12.4 (logs/campaign_{campaign_id}.log).
    """
    constants.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger_name = f"campaign.{campaign_id}"
    campaign_logger = logging.getLogger(logger_name)
    campaign_logger.setLevel(logging.DEBUG)

    # Only add FileHandler if one doesn't exist for this campaign log file yet
    log_file_path = constants.LOGS_DIR / f"campaign_{campaign_id}.log"
    has_file_handler = any(
        isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == str(log_file_path.resolve())
        for h in campaign_logger.handlers
    )

    if not has_file_handler:
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [campaign_id=" + campaign_id + "] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        file_handler.setFormatter(formatter)

        current_settings = settings or get_settings()
        redaction_filter = LogRedactionFilter(known_secret=current_settings.llm_api_key)
        file_handler.addFilter(redaction_filter)
        campaign_logger.addHandler(file_handler)

    return campaign_logger
