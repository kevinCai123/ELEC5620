from __future__ import annotations

from app.services.google_calendar import _sanitize_event_id


def test_sanitize_event_id_filters_invalid_characters() -> None:
    assert _sanitize_event_id("Test UID@123") == "testuid123"


def test_sanitize_event_id_enforces_min_length() -> None:
    assert _sanitize_event_id("abc") == "abcev"
