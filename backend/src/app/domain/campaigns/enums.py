"""Campaign domain enumerations."""

from enum import Enum


class CampaignStatus(str, Enum):
    """
    Trạng thái vòng đời của Campaign theo docs/api-contract.md.
    Kế thừa str, Enum để serialize trực tiếp sang chuỗi JSON.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
