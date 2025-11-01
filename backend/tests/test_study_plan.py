from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from icalendar import Calendar

from app.api.routes.study import (
    _build_plan_calendar,
    build_plan_cancel_calendar,
    build_plan_update_calendar,
)
from app.models.entities import PlanItem
from app.services.study import generate_plan_item_uid


def test_plan_item_uid_idempotent() -> None:
    uid_one = generate_plan_item_uid(1, 42)
    uid_two = generate_plan_item_uid(1, 42)
    assert uid_one == uid_two
    assert uid_one == "59ccdc4f-f0da-50fc-8ddb-6e4eaaaf043a"


def _sample_plan_item(sequence: int = 0) -> PlanItem:
    due_at = datetime(2025, 11, 8, 6, 5, tzinfo=ZoneInfo("Australia/Sydney"))
    return PlanItem(
        plan_id=1,
        title="testing",
        due_at=due_at,
        uid="sample-uid",
        sequence=sequence,
    )


def test_build_plan_calendar_contains_required_fields() -> None:
    plan_item = _sample_plan_item()
    plan = SimpleNamespace(title="Plan: testing", items=[plan_item])
    calendar_text = _build_plan_calendar(
        plan,
        organizer_email="organizer@example.com",
        recipient_email="attendee@example.com",
        event_tz=ZoneInfo("Australia/Sydney"),
    )

    calendar = Calendar.from_ical(calendar_text)
    assert calendar.get("method") == "REQUEST"

    events = [component for component in calendar.walk() if component.name == "VEVENT"]
    assert len(events) == 1
    event = events[0]

    assert str(event.get("uid")) == plan_item.uid
    assert event.get("sequence") == 0
    assert event.get("summary") == "Plan: testing: testing"
    assert event.get("dtstamp") is not None
    assert event.get("dtstart") is not None
    assert event.get("dtend") is not None
    assert event.get("organizer") == "mailto:organizer@example.com"
    attendees = event.get("attendee")
    assert attendees is not None
    assert "attendee@example.com" in str(attendees)


def test_build_plan_update_calendar_increments_sequence() -> None:
    plan_item = _sample_plan_item(sequence=2)
    plan = SimpleNamespace(title="Plan Update", items=[plan_item])
    calendar_text = build_plan_update_calendar(
        plan,
        updated_items=[plan_item],
        organizer_email="organizer@example.com",
        recipient_email="attendee@example.com",
        event_tz=ZoneInfo("Australia/Sydney"),
    )

    calendar = Calendar.from_ical(calendar_text)
    assert calendar.get("method") == "REQUEST"
    event = next(component for component in calendar.walk() if component.name == "VEVENT")
    assert event.get("sequence") == 3
    assert plan_item.sequence == 3


def test_build_plan_cancel_calendar_marks_cancelled() -> None:
    plan_item = _sample_plan_item(sequence=1)
    plan = SimpleNamespace(title="Plan Cancel", items=[plan_item])
    calendar_text = build_plan_cancel_calendar(
        plan,
        items_to_cancel=[plan_item],
        organizer_email="organizer@example.com",
        recipient_email="attendee@example.com",
        event_tz=ZoneInfo("Australia/Sydney"),
    )

    calendar = Calendar.from_ical(calendar_text)
    assert calendar.get("method") == "CANCEL"
    event = next(component for component in calendar.walk() if component.name == "VEVENT")
    assert event.get("status") == "CANCELLED"
    assert event.get("sequence") == 2
    assert plan_item.sequence == 2
