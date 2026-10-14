"""Base interface for all data collectors."""

from abc import ABC, abstractmethod
from typing import Any

from app.collectors.models import RawLeadRecord


class BaseCollector(ABC):
    """Abstract base class defining the contract for data collectors."""

    @abstractmethod
    def collect(self, config: dict[str, Any]) -> list[RawLeadRecord]:
        """
        Collect raw input records matching the campaign configuration.

        Args:
            config: Campaign configuration containing industry, scope, province, max_records.

        Returns:
            A list of RawLeadRecord instances.
        """
        raise NotImplementedError
