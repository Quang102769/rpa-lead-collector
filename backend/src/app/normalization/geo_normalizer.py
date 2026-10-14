"""Deterministic geographic normalizer for province names and addresses."""

from copy import deepcopy
import json
import logging
from pathlib import Path
import re
from typing import Any

from app.collectors.models import RawLeadRecord
from app.core import constants
from app.core.exceptions import ConfigError

logger = logging.getLogger(__name__)

# Administrative prefixes to strip during province name sanitization
ADMIN_PREFIXES: list[str] = [
    "thành phố",
    "thanh pho",
    "tỉnh",
    "tinh",
    "tp.",
    "tp ",
    "t.",
]


class GeoNormalizer:
    """Normalizes province fields using an authoritative reference directory."""

    def __init__(
        self,
        reference_path: Path | None = None,
        reference_data: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize normalizer with reference data.

        Supports dependency injection of custom reference_path or reference_data for tests.
        """
        self._reference_metadata: dict[str, Any] = {}
        self._alias_to_canonical: dict[str, str] = {}
        self._sorted_aliases: list[str] = []
        self._address_regex: re.Pattern[str] | None = None

        if reference_data is not None:
            self._load_from_dict(reference_data)
        else:
            path = reference_path or (
                constants.BACKEND_DIR / "data" / "provinces_reference.json"
            )
            self._load_from_file(path)

    def normalize_lead(self, lead: RawLeadRecord) -> RawLeadRecord:
        """
        Normalize geographic information for a single RawLeadRecord.

        Priority order:
        1. Try to normalize lead.province.
        2. If lead.province is missing or unmatched, scan lead.address with word-boundary matching.
        3. If neither matches or if ambiguous, set province = None (never guess).

        Bảo toàn dữ liệu gốc: input lead is not mutated, raw_payload is copied and
        annotated with raw_geo audit metadata.
        """
        # 1. Safely copy raw_payload without modifying the original
        new_payload = deepcopy(lead.raw_payload) if lead.raw_payload else {}

        # 2. Priority check
        canonical_province: str | None = None
        matched_from: str = "unresolved"

        # Step 2.1: Try province field
        if lead.province:
            canonical_province = self.normalize_province_name(lead.province)
            if canonical_province:
                matched_from = "province"

        # Step 2.2: Fallback to scanning address if province was missing or unresolved
        if not canonical_province and lead.address:
            canonical_province = self.extract_province_from_address(lead.address)
            if canonical_province:
                matched_from = "address"

        # 3. Add raw_geo audit metadata; preserve existing raw_geo into history trail
        current_geo = {
            "original_province": lead.province,
            "original_address": lead.address,
            "matched_from": matched_from,
            "canonical_province": canonical_province,
        }

        if "raw_geo" in new_payload and isinstance(new_payload["raw_geo"], dict):
            # Archive previous raw_geo into history trail to maintain full provenance
            history = new_payload.setdefault("raw_geo_history", [])
            if isinstance(history, list):
                history.append(new_payload["raw_geo"])

        new_payload["raw_geo"] = current_geo

        # 4. Return new RawLeadRecord with canonical province and untouched address
        return RawLeadRecord(
            company_name=lead.company_name,
            industry=lead.industry,
            sub_industry=lead.sub_industry,
            province=canonical_province,
            address=lead.address,
            website=lead.website,
            public_email=lead.public_email,
            public_phone=lead.public_phone,
            description=lead.description,
            source_url=lead.source_url,
            collected_at=lead.collected_at,
            raw_payload=new_payload,
        )

    def normalize_batch(
        self, leads: list[RawLeadRecord]
    ) -> list[RawLeadRecord]:
        """Normalize a batch of RawLeadRecord instances."""
        return [self.normalize_lead(lead) for lead in leads]

    def normalize_province_name(self, raw_province: str | None) -> str | None:
        """
        Normalize a raw province string to its canonical name.

        Performs:
        - Whitespace and punctuation stripping.
        - Administrative prefix removal ('Tỉnh', 'Thành phố', 'TP.').
        - Alias lookup against authoritative directory.
        """
        if not isinstance(raw_province, str) or not raw_province.strip():
            return None

        clean = raw_province.strip()
        lower = clean.lower()

        # Direct alias match first
        if lower in self._alias_to_canonical:
            return self._alias_to_canonical[lower]

        # Strip administrative prefixes
        for prefix in ADMIN_PREFIXES:
            if lower.startswith(prefix):
                stripped = lower[len(prefix):].strip()
                # Remove possible leading dot or dash
                stripped = stripped.lstrip(".-").strip()
                if stripped in self._alias_to_canonical:
                    return self._alias_to_canonical[stripped]

        return None

    def extract_province_from_address(
        self, raw_address: str | None
    ) -> str | None:
        """
        Extract a single unambiguous province from an address string.

        Uses:
        - Word-boundary matching to prevent false substring matches (e.g., 'An' in 'Thuận An').
        - Resolves to None if multiple different provinces match (ambiguous).
        - Resolves to None if no matches are found.
        """
        if not isinstance(raw_address, str) or not raw_address.strip():
            return None

        if not self._address_regex:
            return None

        matches = self._address_regex.finditer(raw_address)
        found_provinces: set[str] = set()

        for match in matches:
            matched_text = match.group(0).lower().strip()
            # Normalize possible punctuation inside match
            clean_match = matched_text.strip(" ,.-")
            canonical = self._alias_to_canonical.get(clean_match)
            if canonical:
                found_provinces.add(canonical)

        # Unambiguous match: exactly 1 distinct canonical province
        if len(found_provinces) == 1:
            return next(iter(found_provinces))

        # Ambiguous (multiple provinces found) or not found -> return None
        return None

    def _load_from_file(self, path: Path) -> None:
        """Load provinces reference data from a JSON file."""
        target_path = path
        if not target_path.is_file():
            # Try secondary fallback path
            fallback = constants.BACKEND_DIR.parent / "data" / "provinces_reference.json"
            if fallback.is_file():
                target_path = fallback
            else:
                raise FileNotFoundError(
                    f"Không tìm thấy tệp danh mục tham chiếu tỉnh thành: '{path}'."
                )

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ConfigError(
                message="Tệp danh mục tham chiếu tỉnh thành bị lỗi cú pháp JSON.",
                detail=f"Tệp: '{target_path}'. Chi tiết lỗi: {exc}",
            ) from exc
        except Exception as exc:
            raise ConfigError(
                message="Không thể đọc tệp danh mục tham chiếu tỉnh thành.",
                detail=f"Tệp: '{target_path}'. Chi tiết lỗi: {exc}",
            ) from exc

        self._load_from_dict(data, source_path=target_path)

    def _load_from_dict(
        self, data: dict[str, Any], source_path: Path | None = None
    ) -> None:
        """Parse reference dictionary and build index structures."""
        if (
            not isinstance(data, dict)
            or "provinces" not in data
            or not isinstance(data["provinces"], list)
        ):
            src_info = f" từ '{source_path}'" if source_path else ""
            raise ConfigError(
                message="Cấu trúc danh mục tham chiếu tỉnh thành không hợp lệ.",
                detail=f"Dữ liệu{src_info} phải là một dictionary chứa khóa 'provinces' kiểu list.",
            )

        self._reference_metadata = {
            "version": data.get("version"),
            "source_reference": data.get("source_reference"),
            "last_updated": data.get("last_updated"),
            "total_count": data.get("total_count"),
        }

        self._alias_to_canonical = {}
        all_aliases: set[str] = set()

        for item in data.get("provinces", []):
            full_name = item.get("name", "").strip()
            if not full_name:
                continue

            # Determine canonical business name
            canonical = self._derive_canonical_name(full_name)

            # Map canonical name and full name
            self._alias_to_canonical[canonical.lower()] = canonical
            self._alias_to_canonical[full_name.lower()] = canonical
            all_aliases.add(canonical)
            all_aliases.add(full_name)

            # Map all declared aliases
            for alias in item.get("aliases", []):
                alias_clean = alias.strip()
                if alias_clean:
                    self._alias_to_canonical[alias_clean.lower()] = canonical
                    all_aliases.add(alias_clean)

                    # Support space-free variants per data-dictionary (e.g., 'danang', 'hanoi')
                    if " " in alias_clean:
                        no_space = alias_clean.replace(" ", "").lower()
                        if len(no_space) >= 4 and "." not in no_space:
                            self._alias_to_canonical[no_space] = canonical
                            all_aliases.add(no_space)

        # Sort aliases by descending length so specific/longer aliases match first
        self._sorted_aliases = sorted(all_aliases, key=len, reverse=True)

        if self._sorted_aliases:
            # Word-boundary regex avoiding partial word matches
            escaped = [re.escape(a) for a in self._sorted_aliases]
            self._address_regex = re.compile(
                r"(?<![\w])(" + "|".join(escaped) + r")(?![\w])",
                re.IGNORECASE,
            )

    def _derive_canonical_name(self, full_name: str) -> str:
        """Derive standard canonical business name from full administrative name."""
        clean = full_name.strip()

        # Standard canonical forms
        if clean == "Thành phố Hồ Chí Minh":
            return "Hồ Chí Minh"
        if clean.startswith("Thành phố "):
            return clean[len("Thành phố "):].strip()
        if clean.startswith("Tỉnh "):
            return clean[len("Tỉnh "):].strip()

        return clean
