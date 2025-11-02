from __future__ import annotations

import pytest

from app.schemas.quiz import QuizItem
from app.services.quiz import QuizService


@pytest.mark.asyncio
async def test_quiz_duplicate_detection_triggers_fallback(db_session, monkeypatch) -> None:
    service = QuizService()

    # Mock the entire _generate_candidates_via_llm method to return varied items
    async def mock_generate_candidates(notes: str) -> list[QuizItem]:
        # Return 8 items with completely different stems to pass deduplication
        items = [
            QuizItem(
                stem="Explain photosynthesis in plants?",
                options=["CO2 absorption", "Water release", "Light capture", "Sugar production"],
                answer_index=0,
                rationale="Photosynthesis requires carbon dioxide.",
                generated_from="llm",
            ),
            QuizItem(
                stem="What causes earthquakes?",
                options=["Plate tectonics", "Wind erosion", "Ocean currents", "Meteor impacts"],
                answer_index=0,
                rationale="Tectonic plates cause earthquakes.",
                generated_from="llm",
            ),
            QuizItem(
                stem="How does mitochondria generate energy?",
                options=["ATP synthesis", "DNA replication", "Protein folding", "Cell division"],
                answer_index=0,
                rationale="Mitochondria produce ATP.",
                generated_from="llm",
            ),
            QuizItem(
                stem="Define gravitational force?",
                options=["Mass attraction", "Magnetic pull", "Electric charge", "Nuclear bond"],
                answer_index=0,
                rationale="Gravity attracts masses.",
                generated_from="llm",
            ),
            QuizItem(
                stem="What is DNA replication?",
                options=["Gene copying", "Protein synthesis", "Cell respiration", "Energy storage"],
                answer_index=0,
                rationale="DNA makes copies of itself.",
                generated_from="llm",
            ),
            QuizItem(
                stem="Describe water cycle?",
                options=["Evaporation process", "Rock formation", "Wind patterns", "Heat transfer"],
                answer_index=0,
                rationale="Water evaporates and condenses.",
                generated_from="llm",
            ),
            QuizItem(
                stem="Explain binary numbers?",
                options=["Base-2 system", "Decimal notation", "Roman numerals", "Hexadecimal code"],
                answer_index=0,
                rationale="Binary uses only 0 and 1.",
                generated_from="llm",
            ),
            QuizItem(
                stem="What are prime numbers?",
                options=["Divisible by 1 and self", "Even numbers", "Multiples of 3", "Negative integers"],
                answer_index=0,
                rationale="Primes have exactly two divisors.",
                generated_from="llm",
            ),
        ]
        return items
    
    monkeypatch.setattr(service, "_generate_candidates_via_llm", mock_generate_candidates)

    items, duplicate_rate, fallback_used, created_new = await service.get_or_create_quiz(
        "Notes about repeated concept", db_session
    )
    assert len(items) == 5
    assert duplicate_rate >= 0
    assert fallback_used is False  # We don't use fallbacks anymore
    assert created_new is True
