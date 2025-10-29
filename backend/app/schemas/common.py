from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class HealthResponse(BaseSchema):
    status: str = "ok"
    version: str = "0.1.0"


class RequestMetadata(BaseSchema):
    request_id: str
    latency_ms: float


class ErrorResponse(BaseSchema):
    detail: str
    metadata: dict[str, Any] | None = Field(default=None)


class DateTimeRange(BaseSchema):
    start: datetime
    end: datetime
