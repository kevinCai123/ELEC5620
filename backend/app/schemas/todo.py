from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import Field, field_serializer

from app.schemas.common import BaseSchema


class TodoExtractRequest(BaseSchema):
    text: str = Field(min_length=1, max_length=5000)
    source: str | None = Field(default=None)


class TodoDraft(BaseSchema):
    title: str
    due_at: datetime | None = None
    due_at_confidence: str | None = None

    @field_serializer("due_at")
    def serialize_due_at(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat()


class TodoCreateItem(BaseSchema):
    title: str
    due_at: datetime | None = None
    due_at_confidence: str | None = None
    source: str | None = None


class TodoCreateRequest(BaseSchema):
    tasks: List[TodoCreateItem]


class TodoResponse(BaseSchema):
    id: int
    title: str
    due_at: datetime | None
    due_at_confidence: str | None
    status: str


class TodoListResponse(BaseSchema):
    todos: List[TodoResponse]


class TodoExtractResponse(BaseSchema):
    drafts: List[TodoDraft]
