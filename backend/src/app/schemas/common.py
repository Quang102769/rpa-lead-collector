
"""Common API schemas and standard response envelopes."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ValidationErrorItem(BaseModel):
    """Details for a single field validation error."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(min_length=1)
    message: str = Field(min_length=1)
    input_value: Any | None = None


class ErrorDetail(BaseModel):
    """Payload for a standard API error."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    detail: str | None = None
    stage: str | None = None
    timestamp: str = Field(min_length=1)
    path: str = Field(min_length=1)
    validation_errors: list[ValidationErrorItem] | None = None


class StandardErrorResponse(BaseModel):
    """Standardized envelope for all HTTP 4xx/5xx responses."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    success: bool = Field(default=False, repr=False)
    error: ErrorDetail


class EnvelopeResponse(BaseModel, Generic[T]):
    """Generic success envelope."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    data: T