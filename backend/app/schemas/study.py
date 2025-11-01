from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import EmailStr, Field, HttpUrl, ValidationInfo, field_validator

from app.schemas.common import BaseSchema


class StudyPlanItemRequest(BaseSchema):
    title: str = Field(min_length=1, max_length=255)
    due_at: datetime

    @field_validator("due_at")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            msg = "due_at must include timezone information"
            raise ValueError(msg)
        return value


class StudyPlanCreateRequest(BaseSchema):
    title: str = Field(min_length=1, max_length=255)
    items: List[StudyPlanItemRequest] = Field(min_length=1, max_length=5)
    created_by: str | None = Field(default=None, max_length=128)
    recipient_email: EmailStr | None = None


class StudyPlanCreateResponse(BaseSchema):
    plan_id: int
    email_sent: bool = False


class StudyPlanItemResponse(BaseSchema):
    id: int
    title: str
    due_at: datetime
    uid: str


class StudyPlanResponse(BaseSchema):
    id: int
    title: str
    created_by: str | None
    created_at: datetime
    items: List[StudyPlanItemResponse]


class SummarizeRequest(BaseSchema):
    text: str | None = Field(default=None, description="Raw text to summarise")
    url: HttpUrl | None = Field(default=None, description="URL to summarise")
    user_request: str | None = Field(
        default="auto",
        description="Specific task for the summariser (e.g., extract links, summarise, answer questions)",
        max_length=500,
    )

    @field_validator("text")
    @classmethod
    def validate_text_or_url(cls, value: str | None, info: ValidationInfo) -> str | None:
        if not value and not info.data.get("url"):
            msg = "Either text or url must be provided"
            raise ValueError(msg)
        return value


class SummarySection(BaseSchema):
    heading: str
    bullets: List[str]


class SummaryQnASeed(BaseSchema):
    q: str
    a_hint: str


class SummaryNote(BaseSchema):
    tldr: str
    sections: List[SummarySection]
    qna_seeds: List[SummaryQnASeed]


class SummarizeResponse(BaseSchema):
    summary: SummaryNote
    fallback_used: bool = False
    truncated: bool = False
