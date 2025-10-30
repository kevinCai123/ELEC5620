from __future__ import annotations

import logging
import re
from html import unescape

import httpx
from pydantic import HttpUrl

from app.schemas.study import SummaryNote
from app.utils.metrics import emit_metric, time_metric
from app.services.llm import LLMService

MAX_CHARS = 20000  # approx 5k tokens


class SummaryService:
    def __init__(self) -> None:
        self._llm = LLMService()

    async def _summarize_cached(self, text: str, user_request: str) -> tuple[SummaryNote, bool]:
        with time_metric("p95_latency_ms", feature="summary"):
            llm_result = await self._llm.summarize(text, user_request=user_request)
        return llm_result.data, llm_result.fallback_used

    async def summarize(
        self,
        text: str | None = None,
        url: str | HttpUrl | None = None,
        user_request: str | None = None,
    ) -> tuple[SummaryNote, bool, bool]:
        if not text and not url:
            msg = "Either text or url must be provided"
            raise ValueError(msg)

        source_text = text
        truncated = False
        if url:
            source_text = await self._fetch_url(url)

        if source_text is None:
            msg = "Unable to obtain source material"
            raise ValueError(msg)
        source_text = self._normalise_source(source_text)

        resolved_request = (user_request or "auto").strip() or "auto"

        if len(source_text) > MAX_CHARS:
            truncated = True
            source_text = source_text[:MAX_CHARS] + " …[truncated]"

        try:
            summary, fallback_used = await self._summarize_cached(source_text, resolved_request)
            emit_metric("fallback_rate", 1.0 if fallback_used else 0.0, feature="summary")
            emit_metric("schema_valid_rate", 1.0, feature="summary")
            return summary, fallback_used, truncated
        except Exception as exc:  # noqa: BLE001
            emit_metric("fallback_rate", 1.0, feature="summary")
            logging.getLogger(__name__).warning("LLM summarization failed: %s", exc)

        fallback_summary = self._llm._fallback_summary(source_text)  # type: ignore[attr-defined]
        return fallback_summary, True, truncated

    async def _fetch_url(self, url: str | HttpUrl) -> str:
        if isinstance(url, HttpUrl):
            url = str(url)
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def _normalise_source(self, source: str) -> str:
        if "<" not in source or ">" not in source:
            return source.strip()
        target = source
        main_match = re.search(r"<main[^>]*>(.*?)</main>", source, flags=re.IGNORECASE | re.DOTALL)
        if main_match:
            target = main_match.group(1)
        target = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", target, flags=re.IGNORECASE | re.DOTALL)
        target = re.sub(r"<!--.*?-->", " ", target, flags=re.DOTALL)
        target = re.sub(r"<[^>]+>", " ", target)
        target = unescape(target)
        target = re.sub(r"\s+", " ", target)
        cleaned = target.strip()
        return cleaned or source.strip()


__all__ = ["SummaryService"]
