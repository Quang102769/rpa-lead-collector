"""Deterministic schema and business rules validator for raw lead records."""

from collections.abc import Callable
from datetime import datetime, timezone
import html
import re
from typing import Any
import urllib.parse

from app.collectors.models import RawLeadRecord
from app.core import constants
from app.core.exceptions import ConfigError
from app.validation.models import (
    FieldError,
    LeadValidationItemResult,
    ValidationBatchResult,
    ValidationStatus,
)

# Canonical industry set supported by the platform
VALID_INDUSTRIES: set[str] = {"Education", "Manufacturing"}

# Case-insensitive blacklist for company name placeholders
BLACKLIST_COMPANY_NAMES: set[str] = {
    "n/a",
    "na",
    "none",
    "null",
    "unknown",
    "chưa có tên",
    "chua co ten",
    "không rõ",
    "khong ro",
    "tbd",
    "undefined",
    "-",
}

# Regex patterns per data-dictionary specifications
URL_REGEX: re.Pattern[str] = re.compile(
    r"^https?://([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(/.*)?$",
    re.IGNORECASE,
)
DOMAIN_PREFIX_REGEX: re.Pattern[str] = re.compile(
    r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(/.*)?$",
    re.IGNORECASE,
)
EMAIL_REGEX: re.Pattern[str] = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)
PHONE_CLEAN_REGEX: re.Pattern[str] = re.compile(r"[\s\.\-\(\)/]")
PHONE_REGEX: re.Pattern[str] = re.compile(r"^\+?[0-9]{8,15}$")
TAGS_REGEX: re.Pattern[str] = re.compile(r"<[^>]+>")

# Blacklist for dummy/placeholder emails per data-dictionary
BLACKLIST_EMAILS: set[str] = {
    "test@example.com",
    "admin@localhost",
    "none@none.com",
    "test@test.com",
    "admin@domain.com",
}


def _strip_tags(text: str) -> str:
    """Strip basic HTML tags and unescape entities."""
    clean = TAGS_REGEX.sub("", text)
    return html.unescape(clean).strip()


class LeadValidator:
    """Validates raw lead records against the 11-field canonical schema."""

    def __init__(
        self,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """
        Initialize validator with an optional clock provider for deterministic testing.
        """
        self._clock: Callable[[], datetime] = clock or (
            lambda: datetime.now(timezone.utc)
        )

    def validate_one(
        self,
        lead: RawLeadRecord,
        expected_industry: str,
        execution_mode: str = "FIXTURE",
        allowed_domains: list[str] | None = None,
    ) -> LeadValidationItemResult:
        """
        Validate a single raw lead record.

        Creates a sanitized new RawLeadRecord without mutating the input raw_lead.
        """
        self._validate_campaign_industry(expected_industry)

        errors: list[FieldError] = []
        warnings: list[FieldError] = []

        sanitized = RawLeadRecord(
            raw_payload=dict(lead.raw_payload) if lead.raw_payload else {}
        )

        # 1. Validate company_name (Required, Non-nullable)
        self._validate_company_name(lead.company_name, sanitized, errors)

        # 2. Validate industry (Required, Must match campaign)
        self._validate_industry(
            lead.industry, expected_industry, sanitized, errors
        )

        # 3. Validate source_url (Required, Execution-mode and domain aware)
        self._validate_source_url(
            lead.source_url, execution_mode, allowed_domains, sanitized, errors
        )

        # 4. Validate collected_at (Required, Fallback on invalid/missing)
        self._validate_collected_at(lead.collected_at, sanitized, warnings)

        # 5. Graceful validation: website (Optional)
        self._validate_website(lead.website, sanitized, warnings)

        # 6. Graceful validation: public_email (Optional)
        self._validate_email(lead.public_email, sanitized, warnings)

        # 7. Graceful validation: public_phone (Optional)
        self._validate_phone(lead.public_phone, sanitized, warnings)

        # 8. Optional string fields sanitization
        self._sanitize_optional_strings(lead, sanitized)

        # Determine status
        if errors:
            status = ValidationStatus.REJECTED
            output_lead = None
        elif warnings:
            status = ValidationStatus.PARTIAL
            output_lead = sanitized
        else:
            status = ValidationStatus.VALID
            output_lead = sanitized

        return LeadValidationItemResult(
            status=status,
            lead=output_lead,
            raw_lead=lead,
            errors=errors,
            warnings=warnings,
        )

    def validate_batch(
        self,
        leads: list[RawLeadRecord],
        expected_industry: str,
        execution_mode: str = "FIXTURE",
        allowed_domains: list[str] | None = None,
    ) -> ValidationBatchResult:
        """
        Validate a batch of raw lead records.
        """
        self._validate_campaign_industry(expected_industry)

        results = [
            self.validate_one(
                lead=lead,
                expected_industry=expected_industry,
                execution_mode=execution_mode,
                allowed_domains=allowed_domains,
            )
            for lead in leads
        ]

        return ValidationBatchResult(results=results)

    def _validate_campaign_industry(self, expected_industry: str) -> None:
        """Ensure campaign target industry is valid."""
        if expected_industry not in VALID_INDUSTRIES:
            raise ConfigError(
                message="Cấu hình ngành của chiến dịch không hợp lệ.",
                detail=(
                    f"Ngành '{expected_industry}' không thuộc danh mục "
                    f"hỗ trợ ({sorted(VALID_INDUSTRIES)})."
                ),
            )

    def _validate_company_name(
        self,
        raw_val: Any,
        sanitized: RawLeadRecord,
        errors: list[FieldError],
    ) -> None:
        """Validate company_name presence, length and placeholder blacklist."""
        if not isinstance(raw_val, str) or not raw_val.strip():
            errors.append(
                FieldError(
                    field="company_name",
                    error_code=constants.ERR_VAL_REQUIRED_MISSING,
                    message="Tên doanh nghiệp là bắt buộc và không được để trống.",
                    rejected_value=raw_val,
                )
            )
            return

        clean = re.sub(r"\s+", " ", raw_val.strip())
        if (
            len(clean) < 2
            or len(clean) > 255
            or clean.lower() in BLACKLIST_COMPANY_NAMES
        ):
            errors.append(
                FieldError(
                    field="company_name",
                    error_code=constants.ERR_VAL_REQUIRED_MISSING,
                    message=(
                        f"Tên doanh nghiệp '{clean}' không hợp lệ "
                        "(độ dài tối thiểu 2 ký tự, không chấp nhận placeholder)."
                    ),
                    rejected_value=raw_val,
                )
            )
            return

        sanitized.company_name = clean

    def _validate_industry(
        self,
        raw_val: Any,
        expected_industry: str,
        sanitized: RawLeadRecord,
        errors: list[FieldError],
    ) -> None:
        """Validate lead industry matches enum and campaign context."""
        if not isinstance(raw_val, str) or not raw_val.strip():
            errors.append(
                FieldError(
                    field="industry",
                    error_code=constants.ERR_VAL_REQUIRED_MISSING,
                    message="Ngành của bản ghi là bắt buộc.",
                    rejected_value=raw_val,
                )
            )
            return

        clean = raw_val.strip()
        if clean not in VALID_INDUSTRIES:
            errors.append(
                FieldError(
                    field="industry",
                    error_code=constants.ERR_CFG_INVALID,
                    message=(
                        f"Ngành '{clean}' không hợp lệ. "
                        f"Chỉ chấp nhận {sorted(VALID_INDUSTRIES)}."
                    ),
                    rejected_value=raw_val,
                )
            )
            return

        if clean != expected_industry:
            errors.append(
                FieldError(
                    field="industry",
                    error_code=constants.ERR_CONFLICT,
                    message=(
                        f"Ngành của bản ghi ('{clean}') không khớp với "
                        f"ngành của chiến dịch ('{expected_industry}')."
                    ),
                    rejected_value=raw_val,
                )
            )
            return

        sanitized.industry = clean

    def _validate_source_url(
        self,
        raw_val: Any,
        execution_mode: str,
        allowed_domains: list[str] | None,
        sanitized: RawLeadRecord,
        errors: list[FieldError],
    ) -> None:
        """Validate source_url presence and mode-appropriate scheme."""
        if not isinstance(raw_val, str) or not raw_val.strip():
            errors.append(
                FieldError(
                    field="source_url",
                    error_code=constants.ERR_VAL_REQUIRED_MISSING,
                    message="URL nguồn là bắt buộc để truy vết dữ liệu.",
                    rejected_value=raw_val,
                )
            )
            return

        clean = raw_val.strip()

        if clean.startswith("fixture://"):
            if execution_mode == "LIVE":
                errors.append(
                    FieldError(
                        field="source_url",
                        error_code=constants.ERR_SRC_UNAPPROVED,
                        message=(
                            "URL nguồn dạng 'fixture://' không được phép "
                            "sử dụng trong chế độ LIVE."
                        ),
                        rejected_value=raw_val,
                    )
                )
                return
            sanitized.source_url = clean
            return

        parsed = urllib.parse.urlparse(clean)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            # Check allowed domains whitelist in LIVE mode if provided
            if execution_mode == "LIVE" and allowed_domains is not None:
                host = parsed.netloc.lower()
                if host.startswith("www."):
                    host = host[4:]
                normalized_allowed = [
                    d.lower()[4:] if d.lower().startswith("www.") else d.lower()
                    for d in allowed_domains
                ]
                if host not in normalized_allowed and not any(
                    host.endswith("." + d) for d in normalized_allowed
                ):
                    errors.append(
                        FieldError(
                            field="source_url",
                            error_code=constants.ERR_SRC_UNAPPROVED,
                            message=(
                                f"Domain '{parsed.netloc}' của URL nguồn không nằm trong "
                                f"danh sách nguồn LIVE được phép ({allowed_domains})."
                            ),
                            rejected_value=raw_val,
                        )
                    )
                    return
            sanitized.source_url = clean
        else:
            errors.append(
                FieldError(
                    field="source_url",
                    error_code=constants.ERR_CFG_INVALID,
                    message=(
                        f"URL nguồn '{clean}' không đúng định dạng "
                        "(yêu cầu scheme http/https hoặc fixture://)."
                    ),
                    rejected_value=raw_val,
                )
            )

    def _validate_collected_at(
        self,
        raw_val: Any,
        sanitized: RawLeadRecord,
        warnings: list[FieldError],
    ) -> None:
        """Validate ISO 8601 collected_at with fallback to current UTC time."""
        is_valid = False
        if isinstance(raw_val, str) and raw_val.strip():
            clean = raw_val.strip()
            try:
                # Handle standard ISO formats, including Z offset
                datetime.fromisoformat(clean.replace("Z", "+00:00"))
                sanitized.collected_at = clean
                is_valid = True
            except (ValueError, TypeError):
                is_valid = False

        if not is_valid:
            fallback = self._clock().strftime("%Y-%m-%dT%H:%M:%SZ")
            sanitized.collected_at = fallback
            warnings.append(
                FieldError(
                    field="collected_at",
                    error_code="WARN_COLLECTED_AT_FALLBACK",
                    message=(
                        "Thời điểm thu thập thiếu hoặc sai định dạng ISO 8601; "
                        f"đã tự động gán mốc thời gian UTC hiện tại ({fallback})."
                    ),
                    rejected_value=raw_val,
                )
            )

    def _validate_website(
        self,
        raw_val: Any,
        sanitized: RawLeadRecord,
        warnings: list[FieldError],
    ) -> None:
        """Validate website URL syntax with graceful degradation to None."""
        if raw_val is None or (isinstance(raw_val, str) and not raw_val.strip()):
            sanitized.website = None
            return

        if not isinstance(raw_val, str):
            sanitized.website = None
            warnings.append(
                FieldError(
                    field="website",
                    error_code="WARN_INVALID_WEBSITE_FORMAT",
                    message="Website không phải kiểu chuỗi; đã gán None.",
                    rejected_value=raw_val,
                )
            )
            return

        clean = raw_val.strip()
        # Only auto-prefix https:// if it strictly matches a domain name format
        if not clean.startswith(("http://", "https://")):
            if DOMAIN_PREFIX_REGEX.match(clean):
                clean = f"https://{clean}"
            else:
                sanitized.website = None
                warnings.append(
                    FieldError(
                        field="website",
                        error_code="WARN_INVALID_WEBSITE_FORMAT",
                        message=(
                            f"Website '{raw_val}' không đúng định dạng domain/URL hợp lệ; "
                            "đã chuyển về None."
                        ),
                        rejected_value=raw_val,
                    )
                )
                return

        if URL_REGEX.match(clean):
            # Strip trailing slash on bare domain
            parsed = urllib.parse.urlparse(clean)
            if parsed.path == "/":
                clean = clean.rstrip("/")
            sanitized.website = clean
        else:
            sanitized.website = None
            warnings.append(
                FieldError(
                    field="website",
                    error_code="WARN_INVALID_WEBSITE_FORMAT",
                    message=(
                        f"Website '{raw_val}' không đúng định dạng URL hợp lệ; "
                        "đã chuyển về None."
                    ),
                    rejected_value=raw_val,
                )
            )

    def _validate_email(
        self,
        raw_val: Any,
        sanitized: RawLeadRecord,
        warnings: list[FieldError],
    ) -> None:
        """Validate email format and dummy blacklist with graceful degradation."""
        if raw_val is None or (isinstance(raw_val, str) and not raw_val.strip()):
            sanitized.public_email = None
            return

        if not isinstance(raw_val, str):
            sanitized.public_email = None
            warnings.append(
                FieldError(
                    field="public_email",
                    error_code="WARN_INVALID_EMAIL_FORMAT",
                    message="Email không phải kiểu chuỗi; đã gán None.",
                    rejected_value=raw_val,
                )
            )
            return

        clean = raw_val.strip().lower()
        if (
            EMAIL_REGEX.match(clean)
            and clean not in BLACKLIST_EMAILS
        ):
            sanitized.public_email = clean
        else:
            sanitized.public_email = None
            warnings.append(
                FieldError(
                    field="public_email",
                    error_code="WARN_INVALID_EMAIL_FORMAT",
                    message=(
                        f"Email '{raw_val}' không đúng định dạng RFC 5322 "
                        "hoặc là email placeholder rác; đã chuyển về None."
                    ),
                    rejected_value=raw_val,
                )
            )

    def _validate_phone(
        self,
        raw_val: Any,
        sanitized: RawLeadRecord,
        warnings: list[FieldError],
    ) -> None:
        """Validate phone length and numbers with graceful degradation."""
        if raw_val is None or (isinstance(raw_val, str) and not raw_val.strip()):
            sanitized.public_phone = None
            return

        if not isinstance(raw_val, str):
            sanitized.public_phone = None
            warnings.append(
                FieldError(
                    field="public_phone",
                    error_code="WARN_INVALID_PHONE_FORMAT",
                    message="Số điện thoại không phải kiểu chuỗi; đã gán None.",
                    rejected_value=raw_val,
                )
            )
            return

        # Take primary number if multiple numbers are listed
        first_num = re.split(r"[/,;]", raw_val.strip())[0].strip()
        clean = PHONE_CLEAN_REGEX.sub("", first_num)
        if PHONE_REGEX.match(clean):
            sanitized.public_phone = clean
        else:
            sanitized.public_phone = None
            warnings.append(
                FieldError(
                    field="public_phone",
                    error_code="WARN_INVALID_PHONE_FORMAT",
                    message=(
                        f"Số điện thoại '{raw_val}' không hợp lệ "
                        "(yêu cầu 8-15 chữ số); đã chuyển về None."
                    ),
                    rejected_value=raw_val,
                )
            )

    def _sanitize_optional_strings(
        self,
        lead: RawLeadRecord,
        sanitized: RawLeadRecord,
    ) -> None:
        """Sanitize and safely truncate sub_industry, address, province, description."""
        # sub_industry (max 150)
        if isinstance(lead.sub_industry, str) and lead.sub_industry.strip():
            clean_sub = _strip_tags(lead.sub_industry)
            sanitized.sub_industry = clean_sub[:150].strip() or None
        else:
            sanitized.sub_industry = None

        # province (pass as-is for GeoNormalizer)
        if isinstance(lead.province, str) and lead.province.strip():
            sanitized.province = lead.province.strip()
        else:
            sanitized.province = None

        # address (max 300)
        if isinstance(lead.address, str) and lead.address.strip():
            clean_addr = _strip_tags(lead.address)
            clean_addr = re.sub(r"\s+", " ", clean_addr)
            sanitized.address = clean_addr[:300].strip() or None
        else:
            sanitized.address = None

        # description (max 500)
        if isinstance(lead.description, str) and lead.description.strip():
            clean_desc = _strip_tags(lead.description)
            clean_desc = re.sub(r"\s+", " ", clean_desc)
            if len(clean_desc) > 500:
                clean_desc = clean_desc[:497] + "..."
            sanitized.description = clean_desc.strip() or None
        else:
            sanitized.description = None
