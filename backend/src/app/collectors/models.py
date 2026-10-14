"""Data models for raw collection stage."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class RawLeadRecord:
    """Represents a raw lead record collected from a fixture or live source."""

    company_name: str | None = None
    industry: str | None = None
    sub_industry: str | None = None
    province: str | None = None
    address: str | None = None
    website: str | None = None
    public_email: str | None = None
    public_phone: str | None = None
    description: str | None = None
    source_url: str | None = None
    collected_at: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to canonical dictionary."""
        return {
            "company_name": self.company_name,
            "industry": self.industry,
            "sub_industry": self.sub_industry,
            "province": self.province,
            "address": self.address,
            "website": self.website,
            "public_email": self.public_email,
            "public_phone": self.public_phone,
            "description": self.description,
            "source_url": self.source_url,
            "collected_at": self.collected_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RawLeadRecord":
        """Instantiate from dictionary."""
        return cls(
            company_name=data.get("company_name"),
            industry=data.get("industry"),
            sub_industry=data.get("sub_industry"),
            province=data.get("province"),
            address=data.get("address"),
            website=data.get("website"),
            public_email=data.get("public_email"),
            public_phone=data.get("public_phone"),
            description=data.get("description"),
            source_url=data.get("source_url"),
            collected_at=data.get("collected_at"),
            raw_payload=dict(data),
        )
