from __future__ import annotations

from typing import List, Literal

from pydantic import Field

from app.schemas.common import BaseSchema


class QuizRequest(BaseSchema):
    notes: str = Field(min_length=1, description="Source notes for quiz generation")


class QuizItem(BaseSchema):
    stem: str
    options: List[str]
    answer_index: int
    rationale: str
    generated_from: Literal["llm", "template"] = "llm"


class QuizResponse(BaseSchema):
    items: List[QuizItem]
    duplicate_stem_rate: float
    fallback_used: bool
