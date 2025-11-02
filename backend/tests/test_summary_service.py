from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.schemas.study import SummaryNote, SummarySection
from app.services import summary as summary_module
from app.services.summary import SummaryService


def _dummy_summary(text: str = "Fallback") -> SummaryNote:
    return SummaryNote(
        tldr=text,
        sections=[SummarySection(heading="Section", bullets=[text])],
        qna_seeds=[],
    )


@pytest.mark.asyncio
async def test_summary_service_fallback(monkeypatch) -> None:
    service = SummaryService()
    monkeypatch.setattr(summary_module, "emit_metric", lambda *args, **kwargs: None)
    monkeypatch.setattr(service, "_summarize_cached", AsyncMock(side_effect=RuntimeError("boom")))
    service._llm = SimpleNamespace(_fallback_summary=lambda src: _dummy_summary(src))  # type: ignore[assignment]

    note, fallback_used, truncated = await service.summarize(
        text="<main>  Study content with <strong>HTML</strong>. </main>"
    )

    assert fallback_used is True
    assert truncated is False
    assert note.tldr.startswith("Study content")


@pytest.mark.asyncio
async def test_summary_service_requires_text_or_url() -> None:
    service = SummaryService()
    with pytest.raises(ValueError):
        await service.summarize(text=None, url=None)
