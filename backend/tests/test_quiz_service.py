from __future__ import annotations

import pytest

from app.schemas.quiz import QuizItem
from app.services.llm import LLMResult
from app.services.quiz import QuizService


@pytest.mark.asyncio
async def test_quiz_duplicate_detection_triggers_fallback(db_session, monkeypatch) -> None:
    service = QuizService()

    async def fake_generate_quiz(self, text: str):  # type: ignore[override]
        items = [
            QuizItem(
                stem="Repeated concept",
                options=["A", "B", "C", "D"],
                answer_index=0,
                rationale="Because.",
                generated_from="llm",
            )
            for _ in range(3)
        ]
        return LLMResult(items, fallback_used=False)

    monkeypatch.setattr(service, "_llm", type("Dummy", (), {"generate_quiz": fake_generate_quiz})())

    items, duplicate_rate, fallback_used, created_new = await service.get_or_create_quiz(
        "Notes about repeated concept", db_session
    )
    assert len(items) == 5
    assert duplicate_rate > 0
    assert fallback_used is True
