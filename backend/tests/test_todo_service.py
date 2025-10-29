from __future__ import annotations

import pytest

from app.services.todo import TodoService


@pytest.mark.asyncio
async def test_todo_extraction_parses_due_dates() -> None:
    service = TodoService()
    text = "- Submit lab report by Friday 5pm\n- Prepare slides"
    drafts, fallback_used = await service.extract(text)
    assert drafts, "Should produce at least one draft"
    assert drafts[0].due_at is not None
    assert drafts[0].due_at_confidence in {"high", "low"}
    assert fallback_used is True
