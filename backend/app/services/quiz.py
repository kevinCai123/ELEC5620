from __future__ import annotations

import hashlib
from typing import Iterable, Tuple

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Quiz
from app.schemas.quiz import QuizItem
from app.services.llm import LLMService
from app.utils.metrics import emit_metric, time_metric

_TEMPLATE_POOL: list[QuizItem] = [
    QuizItem(
        stem="What is the central theme of the study material?",
        options=[
            "An overview of the main concepts",
            "A list of unrelated facts",
            "A biography of the author",
            "A set of random definitions",
        ],
        answer_index=0,
        rationale="The material emphasises the main concepts, making option A the best choice.",
        generated_from="template",
    ),
    QuizItem(
        stem="Which limitation is highlighted?",
        options=[
            "Resource constraints",
            "Unlimited funding",
            "Guaranteed success",
            "Irrelevant background noise",
        ],
        answer_index=0,
        rationale="Resource constraints are explicitly mentioned as a limitation.",
        generated_from="template",
    ),
    QuizItem(
        stem="How many multiple-choice questions are produced?",
        options=["Five", "Three", "Two", "Ten"],
        answer_index=0,
        rationale="The requirement is exactly five MCQs.",
        generated_from="template",
    ),
]


class QuizService:
    def __init__(self) -> None:
        self._llm = LLMService()

    async def get_or_create_quiz(
        self, notes: str, session: AsyncSession
    ) -> tuple[list[QuizItem], float, bool, bool]:
        source_hash = hashlib.sha256(notes.encode("utf-8")).hexdigest()
        existing = await session.scalar(select(Quiz).where(Quiz.source_hash == source_hash))
        if existing:
            items = [QuizItem(**item) for item in existing.items_json]
            return items, 0.0, False, False

        with time_metric("p95_latency_ms", feature="quiz"):
            llm_result = await self._llm.generate_quiz(notes)
        items = self._ensure_valid_items(llm_result.data)
        duplicate_rate = self._compute_duplicate_rate(items)
        fallback_used = llm_result.fallback_used or duplicate_rate > 0
        emit_metric("duplicate_stem_rate", duplicate_rate, feature="quiz")
        emit_metric("fallback_rate", 1.0 if fallback_used else 0.0, feature="quiz")

        while len(items) < 5:
            items.append(_TEMPLATE_POOL[len(items) % len(_TEMPLATE_POOL)])
            fallback_used = True

        payload = [item.model_dump() for item in items[:5]]
        quiz = Quiz(source_hash=source_hash, items_json=payload)
        session.add(quiz)
        await session.flush()
        return items[:5], duplicate_rate, fallback_used, True

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
                    rationale=item.rationale.strip(),
                    generated_from=item.generated_from,
                )
            )
        return validated

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


__all__ = ["QuizService"]
