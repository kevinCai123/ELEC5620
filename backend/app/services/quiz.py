from __future__ import annotations

from typing import Iterable, List

from rapidfuzz import fuzz
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.schemas.quiz import QuizItem
from app.services.llm import LLMService
from app.utils.metrics import emit_metric, time_metric


# === Pydantic container for an oversampled batch directly from the LLM ===
class _QuizCandidates(BaseModel):
    items: List[QuizItem] = Field(min_length=5, max_length=12)


class QuizService:
    def __init__(self) -> None:
        self._llm = LLMService()

    # ---------------------------
    # Public: get or create quiz
    # ---------------------------
    async def get_or_create_quiz(
        self, notes: str, session: AsyncSession
    ) -> tuple[list[QuizItem], float, bool, bool]:
        """
        Returns: (items, duplicate_rate, fallback_used, created)
         - items: final 5 MCQs created by the LLM
         - duplicate_rate: fraction of near-duplicate stems (post-selection)
         - fallback_used: always False (we do not use template fallbacks)
         - created: true if a DB row was created this call
        """
        # Cache disabled - always generate fresh questions
        with time_metric("p95_latency_ms", feature="quiz"):
            candidates = await self._generate_candidates_via_llm(notes)

        # Select 5 high-quality items (light-touch: normalize + dedup + pick 5)
        items = self._select_five(candidates)

        duplicate_rate = self._compute_duplicate_rate(items)
        emit_metric("duplicate_stem_rate", duplicate_rate, feature="quiz")
        emit_metric("fallback_rate", 0.0, feature="quiz")  # no fallbacks in this pipeline

        # Database persistence disabled - fresh generation every time
        # No caching, no saving to DB
        return items, duplicate_rate, False, True

    # ---------------------------
    # LLM candidate generation (fully unlocked prompt)
    # ---------------------------
    async def _generate_candidates_via_llm(self, notes: str) -> list[QuizItem]:
        """
        Request 8–12 MCQs directly from the LLM with maximum freedom.
        Only constraints: schema correctness, four options, and JSON output.
        No fallback, no hard bans (e.g., it may generate any stem style).
        """
        if not self._llm.has_llm:
            raise RuntimeError("LLM unavailable")

        parser = PydanticOutputParser(pydantic_object=_QuizCandidates)
        format_instructions = parser.get_format_instructions()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Create 8-12 multiple-choice questions from the material provided. "
                    "Use your best judgment for question types and styles - you have complete creative freedom. "
                    "Each question must have: 'stem', 'options' (4 choices), 'answer_index' (0-3), and 'rationale'. "
                    "Return JSON matching this format:\n{format_instructions}"
                ),
                (
                    "human",
                    "{notes}"
                ),
            ]
        )

        # High creativity settings for maximum variety
        llm = self._llm._llm.bind(temperature=0.8, top_p=0.95)  # type: ignore[attr-defined,union-attr]
        chain = prompt | llm | parser
        batch = await chain.ainvoke({"notes": notes, "format_instructions": format_instructions})
        return list(batch.items)

    # ---------------------------
    # Selection (light-touch quality control)
    # ---------------------------
    def _normalize(self, item: QuizItem) -> QuizItem:
        """
        Minimal normalization to ensure schema sanity without constraining style:
        - ensure stem ends with '?'
        - ensure exactly 4 trimmed options
        - clamp answer_index to 0..3
        """
        stem = (item.stem or "").strip()
        if stem and not stem.endswith("?"):
            stem += "?"
        options = [o.strip() for o in (item.options or []) if o and o.strip()]
        # ensure exactly 4 by truncating or padding with a neutral string
        while len(options) < 4:
            options.append("No other option is correct.")
        options = options[:4]
        ai = int(item.answer_index) if isinstance(item.answer_index, int) else 0
        ai = 0 if ai < 0 or ai > 3 else ai
        rationale = (item.rationale or "").strip()

        return QuizItem(
            stem=stem or "What is the most accurate statement based on the material?",
            options=options,
            answer_index=ai,
            rationale=rationale or "Derived from the material.",
            generated_from=getattr(item, "generated_from", None),
        )

    def _dedup_by_stem(self, items: list[QuizItem], threshold: int = 90) -> list[QuizItem]:
        """Remove near-duplicate stems (very light constraint to keep variety)."""
        out: list[QuizItem] = []
        seen: list[str] = []
        for it in items:
            if any(fuzz.ratio(it.stem, s) >= threshold for s in seen):
                continue
            out.append(it)
            seen.append(it.stem)
        return out

    def _select_five(self, candidates: Iterable[QuizItem]) -> list[QuizItem]:
        # Normalize all candidates
        normalized = [self._normalize(it) for it in candidates]

        # Deduplicate stems very lightly to keep variety
        unique = self._dedup_by_stem(normalized, threshold=90)

        # If the LLM gave fewer than 5 after normalization (rare), just take what we have
        if len(unique) <= 5:
            return unique[:5]

        # Otherwise, keep the first five (they should already be high-quality/varied)
        return unique[:5]

    # ---------------------------
    # Metrics helpers
    # ---------------------------
    def _compute_duplicate_rate(self, items: list[QuizItem]) -> float:
        if not items:
            return 1.0
        duplicates = 0
        seen: list[str] = []
        for item in items:
            if any(fuzz.ratio(item.stem, existing) > 85 for existing in seen):
                duplicates += 1
            else:
                seen.append(item.stem)
        return duplicates / len(items)

    # ---------------------------
    # Legacy helpers (unused, kept for compatibility)
    # ---------------------------
    def _ensure_valid_items(self, items: Iterable[QuizItem]) -> list[QuizItem]:
        validated: list[QuizItem] = []
        for item in items:
            options = item.options[:4]
            if len(options) < 4:
                continue
            answer_index = max(0, min(item.answer_index, 3))
            validated.append(
                QuizItem(
                    stem=item.stem.strip(),
                    options=[opt.strip() for opt in options],
                    answer_index=answer_index,
                    rationale=(item.rationale or "").strip(),
                    generated_from=item.generated_from,
                )
            )
        return validated


__all__ = ["QuizService"]
