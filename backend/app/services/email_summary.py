from __future__ import annotations

import asyncio
import logging
import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from app.core.config import get_settings
from app.schemas.emails import EmailSummary
from app.services.llm import LLMResult, LLMService
from app.utils.metrics import emit_metric
from app.services.gmail import GmailClient, GmailNotConfiguredError

if TYPE_CHECKING:
    from app.services.llm import EmailAnalysis


class EmailService:
    def __init__(self) -> None:
        self._llm = LLMService()
        self._settings = get_settings()
        self._emails = self._load_sample_emails()
        self._gmail_client = self._init_gmail_client()
        self._logger = logging.getLogger(__name__)

    def _load_sample_emails(self) -> list[dict[str, str | None]]:
        data_path = Path(__file__).resolve().parent.parent / "data" / "sample_emails.json"
        with data_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            return []
        normalized: list[dict[str, str | None]] = []
        for entry in data:
            if isinstance(entry, dict):
                normalized.append(
                    {
                        "id": str(entry.get("id", "")),
                        "subject": entry.get("subject"),
                        "sender": entry.get("sender"),
                        "body": entry.get("body"),
                        "original_url": entry.get("original_url"),
                    }
                )
        return normalized

    def _init_gmail_client(self) -> GmailClient | None:
        try:
            return GmailClient(self._settings)
        except GmailNotConfiguredError:
            return None
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).warning("Failed to initialise Gmail client: %s", exc)
            return None

    async def _fetch_source_emails(self, n: int) -> tuple[list[dict[str, str | None]], bool]:
        if self._gmail_client is None:
            return self._emails[:n], True
        try:
            gmail_messages = await asyncio.to_thread(self._gmail_client.fetch_recent_messages, n)
            messages = [
                {
                    "id": message.id,
                    "subject": message.subject,
                    "sender": message.sender,
                    "body": message.body or message.snippet,
                    "original_url": message.web_link,
                }
                for message in gmail_messages
            ]
            if messages:
                return messages, False
        except Exception as exc:  # pragma: no cover - network call
            self._logger.warning("Gmail fetch failed, falling back to sample emails: %s", exc)
        return self._emails[:n], True

    # Cache disabled - always generate fresh email summaries
    async def _cached_top_emails(self, n: int) -> tuple[list[EmailSummary], bool]:
        summaries: list[EmailSummary] = []
        source_emails, fallback_used = await self._fetch_source_emails(n)
        for email in source_emails:
            body = email.get("body") or ""
            subject = email.get("subject") or "(no subject)"
            sender = email.get("sender") or "(unknown sender)"
            email_id = email.get("id") or "unknown"
            llm_result: LLMResult = await self._llm.summarize_email(
                subject=subject, sender=sender, body=body
            )
            fallback_used = fallback_used or llm_result.fallback_used
            
            # Extract structured analysis
            analysis = cast("EmailAnalysis", llm_result.data)
            summaries.append(
                EmailSummary(
                    id=email_id,
                    subject=subject,
                    sender=sender,
                    summary=analysis.summary,
                    key_points=analysis.key_points,
                    category=analysis.category,
                    original_url=email.get("original_url"),
                )
            )
        emit_metric("fallback_rate", 1.0 if fallback_used else 0.0, feature="emails")
        return summaries, fallback_used

    async def get_top_emails(self, n: int) -> tuple[list[EmailSummary], bool]:
        return await self._cached_top_emails(n)


__all__ = ["EmailService"]
