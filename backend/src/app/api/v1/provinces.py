"""Provinces reference API endpoint according to API Contract Section 6.5."""

import json
import logging
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter
from app.core import constants
from app.schemas.province import ProvinceListResponse

logger = logging.getLogger("app")

router = APIRouter(tags=["Provinces"])


@lru_cache(maxsize=1)
def load_provinces_reference() -> dict:
    """
    Load official administrative units from provinces_reference.json.
    Searches backend/data/ and root data/ directory.
    """
    candidates = [
        constants.BACKEND_DIR / "data" / "provinces_reference.json",
        constants.BACKEND_DIR.parent / "data" / "provinces_reference.json",
        Path("data/provinces_reference.json").resolve(),
    ]

    for path in candidates:
        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info("Loaded %d provinces from %s", len(data.get("provinces", [])), path)
                return data
            except Exception as exc:
                logger.warning("Failed to load provinces reference from %s: %s", path, exc)

    logger.error("provinces_reference.json not found in any candidate path.")
    return {
        "version": "2026.1-ADMIN-UNITS",
        "source_reference": "Danh mục đơn vị hành chính cấp tỉnh Việt Nam",
        "last_updated": "2026-07-01",
        "total_count": 0,
        "default_selection": "48",
        "provinces": [],
    }


@router.get(
    "/provinces",
    response_model=ProvinceListResponse,
    summary="Lấy danh mục tỉnh/thành phố tham chiếu",
)
async def get_provinces() -> ProvinceListResponse:
    """
    Endpoint 5: Danh mục 34 đơn vị hành chính cấp tỉnh hiện hành.
    - Cung cấp danh mục tham chiếu cho dropdown bộ lọc địa phương.
    - Bắt buộc hỗ trợ Thành phố Đà Nẵng với mã 48.
    """
    raw_data = load_provinces_reference()
    return ProvinceListResponse(
        success=True,
        data=raw_data,
    )
