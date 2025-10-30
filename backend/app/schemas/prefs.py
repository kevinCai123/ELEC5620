from __future__ import annotations

from datetime import datetime
from typing import Annotated, List

from pydantic import Field

from app.schemas.common import BaseSchema


class DigestPreferenceRequest(BaseSchema):
    user_id: str = Field(min_length=1, max_length=64)
    digest_enabled: bool
    digest_time: Annotated[str, Field(pattern=r"^\d{2}:\d{2}$")]
    timezone: str = Field(default="Australia/Sydney")


class DigestPreferenceResponse(BaseSchema):
    user_id: str
    digest_enabled: bool
    digest_time: str | None
    timezone: str


class DigestPreviewSection(BaseSchema):
    heading: str
    items: List[str]


class DigestPreviewResponse(BaseSchema):
    generated_at: datetime
    sections: List[DigestPreviewSection]
