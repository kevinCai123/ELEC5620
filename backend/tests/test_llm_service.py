from __future__ import annotations

import pytest

from app.services import llm as llm_module
from app.services.llm import LLMService


def test_llm_service_truncate_and_fallback_components(monkeypatch) -> None:
    monkeypatch.setattr(llm_module, "ChatOpenAI", None)
    service = LLMService()

    text, truncated = service._truncate("short text")
    assert text == "short text" and not truncated

    long_text = "x" * (llm_module.MAX_INPUT_CHARS + 5)
    trimmed, flag = service._truncate(long_text)
    assert flag is True
    assert trimmed.endswith("…[truncated]")

    note = service._fallback_summary("Sentence one. Sentence two. Sentence three. Sentence four.")
    assert note.sections[0].heading == "Core Ideas"

    key_points = service._extract_fallback_key_points(
        "Important assignment reminder",
        "This sentence is sufficiently long to be a point. Another detailed sentence that should be captured.",
    )
    assert key_points and "Subject" in key_points[0]

    category = service._categorize_email_fallback("Exam schedule", "Course Coordinator")
    assert category == "academic"


@pytest.mark.asyncio
async def test_llm_service_email_fallback(monkeypatch) -> None:
    monkeypatch.setattr(llm_module, "ChatOpenAI", None)
    service = LLMService()
    result = await service.summarize_email(
        subject="Assignment due reminder",
        sender="Course admin",
        body="Please submit the assignment before Friday evening to avoid penalties.",
    )
    assert result.fallback_used is True
    assert result.data.category == "academic"
