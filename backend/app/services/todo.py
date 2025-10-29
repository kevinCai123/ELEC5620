from __future__ import annotations

from datetime import datetime
from typing import Iterable

import dateparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.models import Todo
from app.schemas.todo import TodoCreateItem, TodoDraft, TodoResponse
from app.services.llm import LLMService
from app.utils.time import utc_now
from app.utils.metrics import emit_metric, time_metric

_SETTINGS = get_settings()
_DEFAULT_TZ = ZoneInfo(_SETTINGS.default_timezone)
_UTC = ZoneInfo("UTC")


def _parse_due_date(raw: str | None) -> tuple[datetime | None, str | None]:
    if not raw:
        return None, None
    parsed = dateparser.parse(
        raw,
        settings={
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
            "TIMEZONE": _SETTINGS.default_timezone,
        },
    )
    if not parsed:
        return None, "low"
    confidence = "high" if parsed.tzinfo else "low"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_DEFAULT_TZ)
    return parsed.astimezone(_UTC), confidence


class TodoService:
    def __init__(self) -> None:
        self._llm = LLMService()

    async def extract(self, text: str) -> tuple[list[TodoDraft], bool]:
        with time_metric("p95_latency_ms", feature="todo"):
            llm_result = await self._llm.extract_todos(text)
        drafts: list[TodoDraft] = []
        for draft in llm_result.data:
            if isinstance(draft, TodoDraft):
                normalized = draft
            else:
                normalized = TodoDraft(**draft)
            due_at = normalized.due_at
            confidence = normalized.due_at_confidence
            if due_at is None:
                due_at, parsed_confidence = _parse_due_date(normalized.title)
                confidence = confidence or parsed_confidence
            else:
                if due_at.tzinfo is None:
                    due_at = due_at.replace(tzinfo=_DEFAULT_TZ)
                due_at = due_at.astimezone(_UTC)
                confidence = confidence or "high"
            drafts.append(
                TodoDraft(
                    title=normalized.title,
                    due_at=due_at,
                    due_at_confidence=confidence or "low",
                )
            )
        if not drafts:
            drafts.append(TodoDraft(title="Review message", due_at=None, due_at_confidence="low"))
        emit_metric("fallback_rate", 1.0 if llm_result.fallback_used else 0.0, feature="todo")
        return drafts, llm_result.fallback_used

    async def create_tasks(
        self, tasks: Iterable[TodoCreateItem], session: AsyncSession
    ) -> list[TodoResponse]:
        created: list[TodoResponse] = []
        for task in tasks:
            due_at = task.due_at
            confidence = task.due_at_confidence
            if isinstance(due_at, datetime):
                if due_at.tzinfo is None:
                    due_at = due_at.replace(tzinfo=_DEFAULT_TZ)
                due_at = due_at.astimezone(_UTC)
            todo = Todo(
                title=task.title,
                due_at=due_at,
                due_at_confidence=confidence or ("high" if due_at else "low"),
                source=task.source,
                status="pending",
            )
            session.add(todo)
            await session.flush()
            created.append(
                TodoResponse(
                    id=todo.id,
                    title=todo.title,
                    due_at=todo.due_at,
                    due_at_confidence=todo.due_at_confidence,
                    status=todo.status,
                )
            )
        return created

    async def list_tasks(self, session: AsyncSession) -> list[TodoResponse]:
        result = await session.scalars(select(Todo).order_by(Todo.created_at.desc()))
        return [
            TodoResponse(
                id=todo.id,
                title=todo.title,
                due_at=todo.due_at,
                due_at_confidence=todo.due_at_confidence,
                status=todo.status,
            )
            for todo in result
        ]


__all__ = ["TodoService"]
