from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema


class TravelAdviceRequest(BaseSchema):
    location: str = Field(min_length=2)
    event_time: datetime = Field(alias="datetime")

    @field_validator("event_time")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            msg = "datetime must include timezone"
            raise ValueError(msg)
        return value


class TravelAdviceResponse(BaseSchema):
    leave_time: datetime
    recommendation: str
    bring_items: list[str]
    route_url: str
    fallback_used: bool = False
