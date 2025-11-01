from __future__ import annotations

import logging
import re
from datetime import timedelta
from typing import Iterable, Optional
from zoneinfo import ZoneInfo

try:  # pragma: no cover - optional dependency import
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    _CALENDAR_IMPORT_ERROR: Exception | None = None
except ImportError as exc:  # pragma: no cover - environment-specific
    build = None  # type: ignore[assignment]
    HttpError = Exception  # type: ignore
    Credentials = None  # type: ignore
    Request = None  # type: ignore
    _CALENDAR_IMPORT_ERROR = exc

from app.core.config import Settings
from app.models import Plan, PlanItem
from app.utils.time import utc_now

LOG = logging.getLogger(__name__)


class GoogleCalendarNotConfiguredError(RuntimeError):
    """Raised when Google Calendar credentials or dependencies are missing."""


def _sanitize_event_id(uid: str) -> str:
    """Google Calendar event ids must be lowercase 5–1024 chars of [a-z0-9_]."""
    if not uid:
        uid = "plan" + utc_now().strftime("%Y%m%d%H%M%S")
    event_id = re.sub(r"[^a-zA-Z0-9_]", "", uid).lower()
    if len(event_id) < 5:
        event_id = (event_id + "evt00")[:5]
    if len(event_id) > 1024:
        event_id = event_id[:1024]
    if not event_id:
        event_id = "plan" + utc_now().strftime("%H%M%S")
    return event_id


class GoogleCalendarClient:
    """Minimal Calendar v3 client that upserts/cancels events using OAuth user credentials."""

    SCOPE = "https://www.googleapis.com/auth/calendar.events"

    def __init__(self, settings: Settings) -> None:
        if _CALENDAR_IMPORT_ERROR is not None:
            raise GoogleCalendarNotConfiguredError(
                "Google Calendar dependencies are missing. Install google-api-python-client, google-auth, and google-auth-oauthlib."
            ) from _CALENDAR_IMPORT_ERROR
        self._settings = settings
        self._service = build("calendar", "v3", credentials=self._build_credentials(), cache_discovery=False)

    def _build_credentials(self) -> Credentials:
        required = (
            "google_client_id",
            "google_client_secret",
            "google_refresh_token",
            "google_api_user_email",
        )
        missing = [name for name in required if not getattr(self._settings, name, None)]
        if missing:
            raise GoogleCalendarNotConfiguredError(
                f"Missing Google Calendar settings: {', '.join(missing)}"
            )

        creds = Credentials(
            token=None,
            refresh_token=self._settings.google_refresh_token,
            client_id=self._settings.google_client_id,
            client_secret=self._settings.google_client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=[self.SCOPE],
        )
        if not creds.valid:
            try:
                creds.refresh(Request())
            except Exception as exc:  # pragma: no cover - external dependency
                raise GoogleCalendarNotConfiguredError(
                    f"Failed to refresh Google credentials: {exc}"
                ) from exc
        return creds

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def upsert_plan_events(
        self,
        plan: Plan,
        *,
        items: Optional[Iterable[PlanItem]] = None,
        event_tz: ZoneInfo,
        attendee_email: Optional[str] = None,
        calendar_id: str = "primary",
        send_updates: str = "all",
    ) -> None:
        """Create or update each plan item as a Calendar event."""
        if build is None:  # pragma: no cover - defensive
            raise GoogleCalendarNotConfiguredError("Google Calendar client library is unavailable.")

        tz_label = getattr(event_tz, "key", str(event_tz))
        plan_items = list(items) if items is not None else list(plan.items)

        for item in plan_items:
            start = item.due_at.astimezone(event_tz).replace(microsecond=0)
            end = (item.due_at + timedelta(hours=1)).astimezone(event_tz).replace(microsecond=0)

            event_id = _sanitize_event_id(item.uid)
            body = {
                "id": event_id,
                "summary": f"{plan.title}: {item.title}",
                "description": f'Milestone "{item.title}" in plan "{plan.title}".',
                "start": {"dateTime": start.isoformat(), "timeZone": tz_label},
                "end": {"dateTime": end.isoformat(), "timeZone": tz_label},
                "attendees": [{"email": attendee_email}] if attendee_email else [],
                "extendedProperties": {
                    "private": {
                        "uid": item.uid,
                        "sequence": str(getattr(item, "sequence", 0)),
                    }
                },
            }

            try:
                self._service.events().insert(
                    calendarId=calendar_id,
                    body=body,
                    sendUpdates=send_updates,
                ).execute()
                LOG.info(
                    "Inserted Google Calendar event id=%s for plan_item_id=%s",
                    event_id,
                    getattr(item, "id", "unknown"),
                )
            except HttpError as exc:
                status = getattr(getattr(exc, "resp", None), "status", None)
                if status == 409:
                    self._service.events().update(
                        calendarId=calendar_id,
                        eventId=event_id,
                        body=body,
                        sendUpdates=send_updates,
                    ).execute()
                    LOG.info(
                        "Updated Google Calendar event id=%s for plan_item_id=%s",
                        event_id,
                        getattr(item, "id", "unknown"),
                    )
                else:
                    raise

    def cancel_plan_events(
        self,
        plan: Plan,
        *,
        items_to_cancel: Iterable[PlanItem],
        calendar_id: str = "primary",
        send_updates: str = "all",
    ) -> None:
        if build is None:  # pragma: no cover - defensive
            raise GoogleCalendarNotConfiguredError("Google Calendar client library is unavailable.")

        for item in items_to_cancel:
            event_id = _sanitize_event_id(item.uid)
            try:
                self._service.events().delete(
                    calendarId=calendar_id,
                    eventId=event_id,
                    sendUpdates=send_updates,
                ).execute()
                LOG.info(
                    "Deleted Google Calendar event id=%s for plan_item_id=%s",
                    event_id,
                    getattr(item, "id", "unknown"),
                )
            except HttpError as exc:
                status = getattr(getattr(exc, "resp", None), "status", None)
                if status == 404:
                    LOG.info("Google Calendar event id=%s not found; skipping delete.", event_id)
                else:
                    raise
