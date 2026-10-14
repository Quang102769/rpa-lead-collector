"""Fixture collector implementation for offline test and demo execution."""

import json
import logging
from pathlib import Path
from typing import Any

from app.collectors.base import BaseCollector
from app.collectors.models import RawLeadRecord
from app.core import constants
from app.core.exceptions import ConfigError, FixtureInvalidFormatError, FixtureMissingError

logger = logging.getLogger("app")


class FixtureCollector(BaseCollector):
    """
    Loads raw lead data from local static fixture files.

    Strict Architectural Guarantees:
    - Offline execution only: Performs zero external network requests.
    - Deterministic file selection: Selects fixture based solely on campaign config (industry/fixture_file).
    - No silent fallback: Raises FixtureMissingError immediately if the requested file is missing.
    - Strict format validation: Raises FixtureInvalidFormatError on malformed JSON or invalid data types.
    - Single responsibility: Does not update campaign store and does not invoke Excel exporters.
    """

    def __init__(self, fixtures_dir: Path | str | None = None) -> None:
        """
        Initialize the fixture collector with a directory path.

        Args:
            fixtures_dir: Path to the directory containing fixture files.
                          Defaults to constants.DEFAULT_FIXTURES_DIR.
        """
        if fixtures_dir is not None:
            self.fixtures_dir = Path(fixtures_dir).resolve()
        else:
            default_dir = constants.DEFAULT_FIXTURES_DIR
            if default_dir.is_dir():
                self.fixtures_dir = default_dir
            else:
                fallback_data_dir = constants.BACKEND_DIR.parent / "data" / "fixtures"
                self.fixtures_dir = fallback_data_dir if fallback_data_dir.is_dir() else default_dir

    def resolve_fixture_path(self, config: dict[str, Any]) -> Path:
        """
        Determine the exact fixture file path from the campaign configuration.

        Args:
            config: Campaign configuration dict.

        Returns:
            Resolved Path to the target fixture file.

        Raises:
            ConfigError: If required configuration attributes are missing or invalid.
        """
        # 1. Custom fixture file override (typically used for testing individual edge cases)
        custom_file = config.get("fixture_file")
        if custom_file:
            custom_path = Path(custom_file)
            if custom_path.is_absolute():
                return custom_path
            return (self.fixtures_dir / custom_path).resolve()

        # 2. Industry-based selection
        industry = config.get("industry")
        if not industry or not isinstance(industry, str):
            raise ConfigError(
                message="Dữ liệu cấu hình chiến dịch không hợp lệ.",
                detail="Cấu hình chiến dịch thiếu trường bắt buộc 'industry' kiểu chuỗi.",
            )

        industry_normalized = industry.strip()
        if industry_normalized == "Education":
            filename = "education.json"
        elif industry_normalized == "Manufacturing":
            filename = "manufacturing.json"
        else:
            raise ConfigError(
                message="Ngành nghề không được hỗ trợ trong Fixture Mode.",
                detail=f"Ngành '{industry}' không hợp lệ. Chỉ chấp nhận 'Education' hoặc 'Manufacturing'.",
            )

        return (self.fixtures_dir / filename).resolve()

    def collect(self, config: dict[str, Any]) -> list[RawLeadRecord]:
        """
        Load and parse fixture data according to the provided campaign configuration.

        Args:
            config: Campaign configuration containing:
                    - industry: "Education" | "Manufacturing" (required if fixture_file omitted)
                    - geographic_scope: "NATIONWIDE" | "PROVINCE" (optional)
                    - target_province: str (optional)
                    - max_records: int (optional limit, 5-50)
                    - fixture_file: str (optional path override)

        Returns:
            A list of RawLeadRecord instances.

        Raises:
            ConfigError: If config is invalid.
            FixtureMissingError: If target fixture file does not exist.
            FixtureInvalidFormatError: If file has invalid JSON or invalid root structure.
        """
        target_file = self.resolve_fixture_path(config)

        logger.info(
            "FixtureCollector bắt đầu nạp dữ liệu: target_file=%s industry=%s",
            target_file,
            config.get("industry"),
        )

        # 1. Kiểm tra sự tồn tại của tệp (Tuyệt đối không silent fallback sang file khác)
        if not target_file.is_file():
            logger.error("Không tìm thấy tệp fixture yêu cầu: %s", target_file)
            raise FixtureMissingError(
                message="Không tìm thấy tệp dữ liệu mẫu.",
                detail=f"Tệp fixture '{target_file.name}' không tồn tại tại đường dẫn '{target_file}'.",
            )

        # 2. Đọc nội dung tệp
        try:
            content = target_file.read_text(encoding="utf-8")
        except Exception as exc:
            logger.error("Không thể đọc tệp fixture '%s': %s", target_file, exc)
            raise FixtureInvalidFormatError(
                message="Không thể đọc tệp dữ liệu mẫu.",
                detail=f"Lỗi khi đọc tệp '{target_file.name}': {exc}",
            ) from exc

        # 3. Phân tích cú pháp JSON
        try:
            raw_data = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error("Lỗi cú pháp JSON trong tệp fixture '%s': %s", target_file, exc)
            raise FixtureInvalidFormatError(
                message="Tệp dữ liệu mẫu không đúng định dạng JSON.",
                detail=f"Lỗi cú pháp JSON tại dòng {exc.lineno}, cột {exc.colno}: {exc.msg}",
            ) from exc

        # 4. Kiểm tra cấu trúc dữ liệu gốc (Bắt buộc phải là list)
        if not isinstance(raw_data, list):
            logger.error(
                "Cấu trúc tệp fixture '%s' không phải list: %s",
                target_file,
                type(raw_data).__name__,
            )
            raise FixtureInvalidFormatError(
                message="Tệp dữ liệu mẫu không đúng định dạng.",
                detail=(
                    f"Dữ liệu gốc trong tệp '{target_file.name}' phải là một mảng JSON (list), "
                    f"nhưng nhận được kiểu '{type(raw_data).__name__}'."
                ),
            )

        # 5. Phân tích từng bản ghi thành RawLeadRecord
        records: list[RawLeadRecord] = []
        for index, item in enumerate(raw_data):
            if not isinstance(item, dict):
                logger.error(
                    "Bản ghi thứ %d trong tệp '%s' không phải JSON object: %s",
                    index,
                    target_file,
                    type(item).__name__,
                )
                raise FixtureInvalidFormatError(
                    message="Tệp dữ liệu mẫu chứa bản ghi không đúng định dạng.",
                    detail=(
                        f"Bản ghi tại vị trí index {index} trong tệp '{target_file.name}' "
                        f"phải là JSON object (dict), nhận được '{type(item).__name__}'."
                    ),
                )
            records.append(RawLeadRecord.from_dict(item))

        # 6. Áp dụng giới hạn max_records nếu có
        max_records = config.get("max_records")
        if isinstance(max_records, int) and max_records > 0:
            records = records[:max_records]

        logger.info(
            "FixtureCollector nạp thành công: %d bản ghi từ tệp '%s'",
            len(records),
            target_file.name,
        )
        return records
