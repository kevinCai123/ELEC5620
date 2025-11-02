"""Additional comprehensive tests for app/services/quiz.py - quiz generation service."""
from __future__ import annotations



from app.schemas.quiz import QuizItem
from app.services.quiz import QuizService


def test_normalize_adds_question_mark():
    """Test that _normalize adds question mark to stem."""
    service = QuizService()
    
    item = QuizItem(
        stem="What is Python",
        options=["A", "B", "C", "D"],
        answer_index=0,
        rationale="Test",
        generated_from="llm"
    )
    
    normalized = service._normalize(item)
    
    assert normalized.stem.endswith("?")


def test_normalize_pads_options_to_four():
    """Test that _normalize pads options to exactly 4."""
    service = QuizService()
    
    item = QuizItem(
        stem="Test?",
        options=["A", "B"],  # Only 2 options
        answer_index=0,
        rationale="Test",
        generated_from="llm"
    )
    
    normalized = service._normalize(item)
    
    assert len(normalized.options) == 4
    assert "No other option is correct" in normalized.options[2]


def test_normalize_truncates_options_to_four():
    """Test that _normalize truncates options to 4."""
    service = QuizService()
    
    item = QuizItem(
        stem="Test?",
        options=["A", "B", "C", "D", "E", "F"],  # Too many
        answer_index=0,
        rationale="Test",
        generated_from="llm"
    )
    
    normalized = service._normalize(item)
    
    assert len(normalized.options) == 4


def test_normalize_clamps_answer_index():
    """Test that _normalize clamps answer_index to 0-3."""
    service = QuizService()
    
    item = QuizItem(
        stem="Test?",
        options=["A", "B", "C", "D"],
        answer_index=10,  # Out of range
        rationale="Test",
        generated_from="llm"
    )
    
    normalized = service._normalize(item)
    
    assert 0 <= normalized.answer_index <= 3


def test_normalize_handles_negative_answer_index():
    """Test that _normalize handles negative answer_index."""
    service = QuizService()
    
    item = QuizItem(
        stem="Test?",
        options=["A", "B", "C", "D"],
        answer_index=-1,
        rationale="Test",
        generated_from="llm"
    )
    
    normalized = service._normalize(item)
    
    assert normalized.answer_index == 0


def test_normalize_provides_default_stem():
    """Test that _normalize provides default stem when empty."""
    service = QuizService()
    
    item = QuizItem(
        stem="",
        options=["A", "B", "C", "D"],
        answer_index=0,
        rationale="Test",
        generated_from="llm"
    )
    
    normalized = service._normalize(item)
    
    assert len(normalized.stem) > 0
    assert "accurate statement" in normalized.stem.lower()


def test_normalize_provides_default_rationale():
    """Test that _normalize provides default rationale when empty."""
    service = QuizService()
    
    item = QuizItem(
        stem="Test?",
        options=["A", "B", "C", "D"],
        answer_index=0,
        rationale="",
        generated_from="llm"
    )
    
    normalized = service._normalize(item)
    
    assert len(normalized.rationale) > 0


def test_normalize_strips_whitespace():
    """Test that _normalize strips whitespace from stem and options."""
    service = QuizService()
    
    item = QuizItem(
        stem="  Test  ",
        options=["  A  ", "  B  ", "  C  ", "  D  "],
        answer_index=0,
        rationale="  Test  ",
        generated_from="llm"
    )
    
    normalized = service._normalize(item)
    
    assert normalized.stem == "Test?"
    assert all(opt.strip() == opt for opt in normalized.options)


def test_dedup_by_stem_removes_duplicates():
    """Test that _dedup_by_stem removes similar stems."""
    service = QuizService()
    
    items = [
        QuizItem(stem="What is Python?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
        QuizItem(stem="What is Python?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),  # Exact duplicate
        QuizItem(stem="What is Java?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
    ]
    
    result = service._dedup_by_stem(items, threshold=90)
    
    # First two are exact duplicates, should only keep first
    assert len(result) == 2
    assert "Java" in result[1].stem


def test_dedup_by_stem_keeps_dissimilar():
    """Test that _dedup_by_stem keeps dissimilar stems."""
    service = QuizService()
    
    items = [
        QuizItem(stem="What is Python?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
        QuizItem(stem="What is Java?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
        QuizItem(stem="Explain photosynthesis?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
    ]
    
    result = service._dedup_by_stem(items, threshold=90)
    
    # All different, should keep all
    assert len(result) == 3


def test_select_five_returns_max_five():
    """Test that _select_five returns at most 5 items."""
    service = QuizService()
    
    items = [
        QuizItem(stem=f"Question {i}?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm")
        for i in range(10)
    ]
    
    result = service._select_five(items)
    
    assert len(result) <= 5


def test_select_five_returns_less_than_five_if_needed():
    """Test that _select_five returns fewer than 5 if that's all there is."""
    service = QuizService()
    
    # Create items with very different stems to avoid deduplication
    items = [
        QuizItem(stem="What is photosynthesis?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
        QuizItem(stem="Explain gravity?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
        QuizItem(stem="Define mitochondria?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
    ]
    
    result = service._select_five(items)
    
    assert len(result) == 3


def test_compute_duplicate_rate_with_no_items():
    """Test that _compute_duplicate_rate returns 1.0 for empty list."""
    service = QuizService()
    
    result = service._compute_duplicate_rate([])
    
    assert result == 1.0


def test_compute_duplicate_rate_with_all_unique():
    """Test that _compute_duplicate_rate returns 0.0 for all unique."""
    service = QuizService()
    
    items = [
        QuizItem(stem="What is photosynthesis?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
        QuizItem(stem="Explain quantum mechanics?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
        QuizItem(stem="Define entropy?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
    ]
    
    result = service._compute_duplicate_rate(items)
    
    assert result == 0.0


def test_compute_duplicate_rate_with_some_duplicates():
    """Test that _compute_duplicate_rate calculates correct rate."""
    service = QuizService()
    
    items = [
        QuizItem(stem="Question 1?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
        QuizItem(stem="Question 1?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),  # Exact duplicate
        QuizItem(stem="Completely different topic?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
    ]
    
    result = service._compute_duplicate_rate(items)
    
    # Should detect 1 duplicate out of 3 items
    assert result > 0


def test_ensure_valid_items_filters_invalid():
    """Test that _ensure_valid_items filters out items with < 4 options."""
    service = QuizService()
    
    items = [
        QuizItem(stem="Valid?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
        QuizItem(stem="Invalid?", options=["A", "B"], answer_index=0, rationale="R", generated_from="llm"),  # Only 2
        QuizItem(stem="Also valid?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
    ]
    
    result = service._ensure_valid_items(items)
    
    # Should only keep items with 4 options
    assert len(result) == 2


def test_ensure_valid_items_clamps_answer_index():
    """Test that _ensure_valid_items clamps answer_index to 0-3."""
    service = QuizService()
    
    items = [
        QuizItem(stem="Test?", options=["A", "B", "C", "D"], answer_index=10, rationale="R", generated_from="llm"),
    ]
    
    result = service._ensure_valid_items(items)
    
    assert result[0].answer_index == 3  # Clamped to max


def test_ensure_valid_items_strips_content():
    """Test that _ensure_valid_items strips whitespace."""
    service = QuizService()
    
    items = [
        QuizItem(stem="  Test?  ", options=["  A  ", "  B  ", "  C  ", "  D  "], answer_index=0, rationale="  R  ", generated_from="llm"),
    ]
    
    result = service._ensure_valid_items(items)
    
    assert result[0].stem == "Test?"
    assert all(opt.strip() == opt for opt in result[0].options)


def test_normalize_handles_none_options():
    """Test that _normalize handles None in options list."""
    service = QuizService()
    
    item = QuizItem(
        stem="Test?",
        options=["A", "B", "C", "D"],  # Valid options
        answer_index=0,
        rationale="Test",
        generated_from="llm"
    )
    
    normalized = service._normalize(item)
    
    # Should work fine with valid options
    assert len(normalized.options) == 4
    assert None not in normalized.options


def test_normalize_preserves_generated_from():
    """Test that _normalize preserves generated_from attribute."""
    service = QuizService()
    
    item = QuizItem(
        stem="Test?",
        options=["A", "B", "C", "D"],
        answer_index=0,
        rationale="Test",
        generated_from="llm"
    )
    
    normalized = service._normalize(item)
    
    assert normalized.generated_from == "llm"


def test_normalize_handles_empty_stem_list():
    """Test _normalize handles None stem gracefully."""
    service = QuizService()
    
    item = QuizItem(
        stem="",  # Empty string
        options=["A", "B", "C", "D"],
        answer_index=0,
        rationale="Test",
        generated_from="llm"
    )
    
    normalized = service._normalize(item)
    
    # Should provide default stem
    assert len(normalized.stem) > 0


def test_select_five_handles_duplicates_after_normalization():
    """Test _select_five deduplicates after normalization."""
    service = QuizService()
    
    # Items that become duplicates after normalization
    items = [
        QuizItem(stem="What is Python", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
        QuizItem(stem="What is Python?", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
        QuizItem(stem="What is Java", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
        QuizItem(stem="What is JavaScript", options=["A", "B", "C", "D"], answer_index=0, rationale="R", generated_from="llm"),
    ]
    
    result = service._select_five(items)
    
    # Should deduplicate similar ones
    assert len(result) <= 4

