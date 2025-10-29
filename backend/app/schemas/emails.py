from __future__ import annotations

from typing import List

from pydantic import Field

from app.schemas.common import BaseSchema


class EmailSummary(BaseSchema):
    id: str
    subject: str
    sender: str
    summary: str = Field(description="1-2 sentence summary of the email")
    key_points: List[str] = Field(default_factory=list, description="Key action items or important points")
    category: str = Field(default="general", description="Email category (e.g., academic, admin, social, promotional)")
    original_url: str | None = None


class TopEmailsResponse(BaseSchema):
    emails: List[EmailSummary]
    fallback_used: bool = False
