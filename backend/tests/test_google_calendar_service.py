from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest
from zoneinfo import ZoneInfo

from app.models.entities import PlanItem
from app.services import google_calendar as gc_module


def _make_plan_item(sequence: int = 0) -> PlanItem:
    return PlanItem(
        plan_id=1,
        title="Unit Test Session",
        due_at=datetime(2025, 5, 12, 9, 30, tzinfo=ZoneInfo("Australia/Sydney")),
        uid="Plan#1@Item!",
        sequence=sequence,
    )


def test_sanitize_event_id_filters_invalid_characters() -> None:
    assert gc_module._sanitize_event_id("Test UID@123") == "testuid123"


def test_sanitize_event_id_enforces_min_length() -> None:
    assert gc_module._sanitize_event_id("abc") == "abcev"


class DummyCredentials:
    def __init__(self, **_: object) -> None:
        self.valid = False

    def refresh(self, _request: object) -> None:
        self.valid = True


class DummyRequest:
    pass


class DummyResponse:
    def __init__(self, status: int) -> None:
        self.status = status


class DummyHttpError(Exception):
    def __init__(self, status: int) -> None:
        self.resp = DummyResponse(status)


class DummyCalendarService:
    def __init__(self) -> None:
        self.insert_calls: list[dict] = []
        self.update_calls: list[dict] = []
        self.delete_calls: list[str] = []
        self._seen_event_ids: set[str] = set()

    def events(self) -> "DummyCalendarService":
        return self

    def insert(self, *, calendarId: str, body: dict, sendUpdates: str) -> "DummyCalendarService":
        if body["id"] in self._seen_event_ids:
            raise DummyHttpError(409)
        self._seen_event_ids.add(body["id"])
        self.insert_calls.append({"calendarId": calendarId, "body": body, "sendUpdates": sendUpdates})
        return self

    def update(self, *, calendarId: str, eventId: str, body: dict, sendUpdates: str) -> "DummyCalendarService":
        self.update_calls.append(
            {"calendarId": calendarId, "eventId": eventId, "body": body, "sendUpdates": sendUpdates}
        )
        return self

    def delete(self, *, calendarId: str, eventId: str, sendUpdates: str) -> "DummyCalendarService":
        if eventId not in self._seen_event_ids:
            raise DummyHttpError(404)
        self._seen_event_ids.remove(eventId)
        self.delete_calls.append(eventId)
        return self

    def execute(self) -> None:  # pragma: no cover - nothing to execute
        return None


@pytest.mark.asyncio
async def test_google_calendar_upsert_and_cancel(monkeypatch) -> None:
    monkeypatch.setattr(gc_module, "_CALENDAR_IMPORT_ERROR", None, raising=False)
    monkeypatch.setattr(gc_module, "Credentials", DummyCredentials)
    monkeypatch.setattr(gc_module, "Request", DummyRequest)
    monkeypatch.setattr(gc_module, "HttpError", DummyHttpError)

    dummy_service = DummyCalendarService()
    monkeypatch.setattr(gc_module, "build", lambda *args, **kwargs: dummy_service)

    settings = SimpleNamespace(
        google_client_id="client",
        google_client_secret="secret",
        google_refresh_token="refresh",
        google_api_user_email="owner@example.com",
        google_calendar_id="primary",
    )
    client = gc_module.GoogleCalendarClient(settings)  # type: ignore[arg-type]

    plan_item = _make_plan_item()
    plan = SimpleNamespace(title="Study Session", items=[plan_item])
    tz = ZoneInfo("Australia/Sydney")

    # First call inserts; second call triggers update path for same event id
    client.upsert_plan_events(plan, event_tz=tz, attendee_email="attendee@example.com")  # type: ignore[arg-type]
    client.upsert_plan_events(plan, event_tz=tz, attendee_email="attendee@example.com")  # type: ignore[arg-type]

    assert dummy_service.insert_calls, "Expected at least one insert call"
    assert dummy_service.update_calls, "Expected update call when event already exists"

    # Cancel once (success) then again to exercise 404 path
    client.cancel_plan_events(plan, items_to_cancel=plan.items, calendar_id="primary", send_updates="none")  # type: ignore[arg-type]
    client.cancel_plan_events(plan, items_to_cancel=plan.items, calendar_id="primary", send_updates="none")  # type: ignore[arg-type]
    assert dummy_service.delete_calls, "Expected delete call for cancelled event"
