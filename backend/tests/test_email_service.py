from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.schemas.emails import EmailSummary
from app.services.email_summary import EmailService
from app.services.llm import LLMResult


class DummyLLM:
    async def summarize_email(self, subject: str, sender: str, body: str) -> LLMResult:
        analysis = SimpleNamespace(summary=f"Summary of {subject}", key_points=[body[:10]], category="academic")
        return LLMResult(data=analysis, fallback_used=False)


@pytest.mark.asyncio
async def test_email_service_uses_sample_emails_when_gmail_missing(monkeypatch) -> None:
    sample = [
        {
            "id": "1",
            "subject": "Lecture reminder",
            "sender": "Professor",
            "body": "Please review the lecture notes before class.",
            "original_url": "https://example.com",
        }
    ]

    monkeypatch.setattr(EmailService, "_load_sample_emails", lambda self: sample)
    monkeypatch.setattr(EmailService, "_init_gmail_client", lambda self: None)

    captured_metrics: list[tuple] = []
    monkeypatch.setattr(
        "app.services.email_summary.emit_metric",
        lambda *args, **kwargs: captured_metrics.append((args, kwargs)),
    )

    service = EmailService()
    service._llm = DummyLLM()  # type: ignore[assignment]

    summaries, fallback_used = await service.get_top_emails(1)

    assert fallback_used is True  # Gmail fallback path used
    assert isinstance(summaries[0], EmailSummary)
    assert summaries[0].summary.startswith("Summary of Lecture")
    assert captured_metrics, "Expected fallback metric to be emitted"
