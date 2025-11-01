from __future__ import annotations

import asyncio
import io
import logging
import smtplib
from collections.abc import Iterable
from datetime import datetime, timedelta
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from icalendar import Calendar, Event, vCalAddress, vText

from app.api.deps import get_db_session, get_quiz_service, get_summary_service
from app.core.config import get_settings
from app.models import Plan, PlanItem
from app.schemas.quiz import QuizRequest, QuizResponse
from app.schemas.study import (
    StudyPlanCreateRequest,
    StudyPlanCreateResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from app.services.quiz import QuizService
from app.services.gmail import GmailClient, GmailNotConfiguredError
from app.services.google_calendar import (
    GoogleCalendarClient,
    GoogleCalendarNotConfiguredError,
)
from app.services.study import generate_plan_item_uid
from app.services.summary import SummaryService
from app.utils.time import utc_now

router = APIRouter()

logger = logging.getLogger(__name__)


def _build_plan_calendar(
    plan: Plan,
    *,
    organizer_email: str | None,
    recipient_email: str,
    event_tz: ZoneInfo,
    items: Iterable[PlanItem] | None = None,
    method: str = "REQUEST",
    status: str | None = None,
) -> str:
    calendar = Calendar()
    calendar.add("prodid", "-//AI Companion Plan//EN")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("method", method.upper())
    calendar.add("X-WR-CALNAME", plan.title)
    calendar.add("X-WR-CALDESC", plan.title)
    tz_label = getattr(event_tz, "key", str(event_tz))
    calendar.add("X-WR-TIMEZONE", tz_label)

    # Ensure all datetimes are timezone-aware before sorting
    def get_aware_due_at(item: PlanItem) -> datetime:
        due_at = item.due_at
        if due_at.tzinfo is None:
            # Treat naive datetimes as UTC
            due_at = due_at.replace(tzinfo=ZoneInfo("UTC"))
        return due_at
    
    selected_items = sorted(
        list(items) if items is not None else list(plan.items),
        key=get_aware_due_at
    )
    for item in selected_items:
        event = Event()
        # Ensure due_at is timezone-aware
        due_at = get_aware_due_at(item)
        start = due_at.astimezone(event_tz).replace(microsecond=0)
        end = (due_at + timedelta(hours=1)).astimezone(event_tz).replace(microsecond=0)
        dtstamp = utc_now().replace(microsecond=0)

        event.add("summary", f"{plan.title}: {item.title}")
        event.add("description", f'Milestone "{item.title}" in plan "{plan.title}".')
        event.add("dtstart", start)
        event.add("dtend", end)
        event.add("dtstamp", dtstamp)
        event.add("uid", item.uid)
        event.add("sequence", getattr(item, "sequence", 0))
        if status:
            event.add("status", status)
        if organizer_email:
            organizer = vCalAddress(f"mailto:{organizer_email}")
            organizer.params["cn"] = vText(organizer_email)
            event["organizer"] = organizer

        attendee = vCalAddress(f"mailto:{recipient_email}")
        attendee.params["cn"] = vText(recipient_email)
        attendee.params["partstat"] = vText("NEEDS-ACTION")
        attendee.params["role"] = vText("REQ-PARTICIPANT")
        attendee.params["rsvp"] = vText("TRUE")
        event.add("attendee", attendee)
        calendar.add_component(event)

    return calendar.to_ical().decode("utf-8")


def build_plan_update_calendar(
    plan: Plan,
    *,
    updated_items: Iterable[PlanItem],
    organizer_email: str | None,
    recipient_email: str,
    event_tz: ZoneInfo,
) -> str:
    items_list = list(updated_items)
    for item in items_list:
        item.sequence = getattr(item, "sequence", 0) + 1
    return _build_plan_calendar(
        plan,
        organizer_email=organizer_email,
        recipient_email=recipient_email,
        event_tz=event_tz,
        items=items_list,
        method="REQUEST",
    )


def build_plan_cancel_calendar(
    plan: Plan,
    *,
    items_to_cancel: Iterable[PlanItem],
    organizer_email: str | None,
    recipient_email: str,
    event_tz: ZoneInfo,
) -> str:
    items_list = list(items_to_cancel)
    for item in items_list:
        item.sequence = getattr(item, "sequence", 0) + 1
    return _build_plan_calendar(
        plan,
        organizer_email=organizer_email,
        recipient_email=recipient_email,
        event_tz=event_tz,
        items=items_list,
        method="CANCEL",
        status="CANCELLED",
    )


def _compose_plan_email_body(plan: Plan, target_tz: ZoneInfo) -> str:
    lines = [f"Plan: {plan.title}", ""]
    # Ensure timezone-aware comparison
    def get_aware_due_at(item: PlanItem) -> datetime:
        due_at = item.due_at
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=ZoneInfo("UTC"))
        return due_at
    
    for item in sorted(plan.items, key=get_aware_due_at):
        due_at = get_aware_due_at(item)
        local_due = due_at.astimezone(target_tz)
        formatted = local_due.strftime("%A, %d %B %Y at %I:%M %p %Z")
        lines.append(f'Milestone "{item.title}" is on {formatted}.')
    lines.extend(
        [
            "",
            "The attached ICS file can be imported into Google Calendar or any compatible calendar app.",
        ]
    )
    return "\n".join(lines)


async def _deliver_plan_email(plan: Plan, recipient_email: str | None) -> bool:
    settings = get_settings()
    target_email = recipient_email or settings.google_api_user_email or settings.smtp_user
    if not target_email:
        logger.info("Skipping plan email dispatch: no recipient email supplied.")
        return False

    target_tz = ZoneInfo(settings.default_timezone)
    organizer_email = settings.google_api_user_email or settings.smtp_user
    calendar_text = _build_plan_calendar(
        plan,
        organizer_email=organizer_email,
        recipient_email=target_email,
        event_tz=target_tz,
    )
    calendar_synced = await _sync_plan_to_google_calendar(
        plan,
        attendee_email=target_email,
        event_tz=target_tz,
    )
    if calendar_synced:
        logger.info("Plan synced to Google Calendar for %s", target_email)
    
    # Ensure timezone-aware comparison for logging
    def get_aware_due_at(item: PlanItem) -> datetime:
        due_at = item.due_at
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=ZoneInfo("UTC"))
        return due_at
    
    for item in sorted(plan.items, key=get_aware_due_at):
        logger.info(
            "Prepared calendar invite uid=%s sequence=%s attendee=%s",
            item.uid,
            getattr(item, "sequence", 0),
            target_email,
        )
    body_text = _compose_plan_email_body(plan, target_tz)
    subject = f"Plan: {plan.title}"

    # Try Gmail first if configured
    try:
        if (
            settings.google_client_id
            and settings.google_client_secret
            and settings.google_refresh_token
        ):
            gmail_sent = await _send_plan_email_via_gmail(
                subject=subject,
                body_text=body_text,
                calendar_text=calendar_text,
                recipient_email=target_email,
            )
            if gmail_sent:
                return True
        else:
            logger.info("Gmail credentials not available; falling back to SMTP if configured.")
    except Exception as exc:  # pragma: no cover - external dependency
        logger.warning("Failed to send plan email via Gmail: %s", exc, exc_info=True)

    # Fall back to SMTP
    smtp_sent = await _send_plan_email_via_smtp(
        subject=subject,
        body_text=body_text,
        calendar_text=calendar_text,
        recipient_email=target_email,
    )
    if smtp_sent:
        return True

    logger.info("Plan email dispatch skipped: no available email transport succeeded.")
    return False


async def _sync_plan_to_google_calendar(
    plan: Plan, *, attendee_email: str, event_tz: ZoneInfo
) -> bool:
    settings = get_settings()
    try:
        client = GoogleCalendarClient(settings)
    except GoogleCalendarNotConfiguredError:
        logger.info("Google Calendar client not configured; skipping calendar sync.")
        return False

    def _sync() -> None:
        client.upsert_plan_events(
            plan,
            items=None,
            event_tz=event_tz,
            attendee_email=attendee_email,
            calendar_id=settings.google_calendar_id or "primary",
            send_updates="all",
        )

    try:
        await asyncio.to_thread(_sync)
        return True
    except Exception as exc:  # pragma: no cover - external dependency
        logger.warning("Failed to sync plan to Google Calendar: %s", exc, exc_info=True)
        return False


async def _send_plan_email_via_gmail(
    *,
    subject: str,
    body_text: str,
    calendar_text: str,
    recipient_email: str,
) -> bool:
    settings = get_settings()
    try:
        client = GmailClient(settings)
    except GmailNotConfiguredError:
        logger.info("Gmail client not configured; skipping Gmail send.")
        return False

    def _send() -> None:
        client.send_email(
            subject=subject,
            body_text=body_text,
            to_email=recipient_email,
            attachments=[
                (
                    "plan.ics",
                    "text/calendar",
                    calendar_text.encode("utf-8"),
                    {"method": "REQUEST", "name": "plan.ics", "charset": "UTF-8"},
                )
            ],
            calendar_alternative=(
                calendar_text,
                {"method": "REQUEST", "charset": "UTF-8", "name": "plan.ics"},
            ),
        )

    try:
        await asyncio.to_thread(_send)
        return True
    except Exception as exc:  # pragma: no cover - external dependency
        logger.warning("Failed to send plan email via Gmail: %s", exc, exc_info=True)
        return False


async def _send_plan_email_via_smtp(
    *,
    subject: str,
    body_text: str,
    calendar_text: str,
    recipient_email: str,
) -> bool:
    settings = get_settings()
    host = settings.smtp_host
    port = settings.smtp_port or (465 if settings.smtp_use_ssl else 587)
    if not host or not port:
        logger.info("SMTP host/port not configured; skipping SMTP send.")
        return False

    from_address = settings.smtp_user or recipient_email
    password = settings.smtp_pass

    message = EmailMessage()
    message["To"] = recipient_email
    message["From"] = from_address
    message["Subject"] = subject
    message.set_content(body_text)
    message.add_alternative(
        calendar_text,
        subtype="calendar",
        params={"method": "REQUEST", "charset": "UTF-8", "name": "plan.ics"},
    )
    message.add_attachment(
        calendar_text,
        maintype="text",
        subtype="calendar",
        filename="plan.ics",
        params={"method": "REQUEST", "name": "plan.ics", "charset": "UTF-8"},
    )

    def _send() -> None:
        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(host, port) as server:
                if password:
                    server.login(from_address, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                if password:
                    server.login(from_address, password)
                server.send_message(message)

    try:
        await asyncio.to_thread(_send)
        return True
    except Exception as exc:  # pragma: no cover - external dependency
        logger.warning("Failed to send plan email via SMTP: %s", exc, exc_info=True)
        return False


@router.post("/plan", response_model=StudyPlanCreateResponse, tags=["plan"])
@router.post("/study/plan", response_model=StudyPlanCreateResponse, tags=["plan"])
async def create_study_plan(
    payload: StudyPlanCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> StudyPlanCreateResponse:
    plan = Plan(title=payload.title, created_by=payload.created_by, created_at=utc_now())
    session.add(plan)
    await session.flush()

    for item in payload.items:
        due_at = item.due_at
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=ZoneInfo("UTC"))
        due_at_utc = due_at.astimezone(ZoneInfo("UTC"))
        plan_item = PlanItem(
            plan_id=plan.id,
            title=item.title,
            due_at=due_at_utc,
            uid="pending",
            sequence=0,
        )
        session.add(plan_item)
        await session.flush()
        plan_item.uid = generate_plan_item_uid(plan.id, plan_item.id)
    await session.commit()

    await session.refresh(plan, attribute_names=["items"])
    email_sent = await _deliver_plan_email(plan, payload.recipient_email)

    return StudyPlanCreateResponse(plan_id=plan.id, email_sent=email_sent)


@router.get("/plan/{plan_id}.ics", tags=["plan"])
@router.get("/study/plan/{plan_id}.ics", tags=["plan"])
async def download_plan_ics(
    plan_id: int = Path(...),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    plan = await session.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    await session.refresh(plan, attribute_names=["items"])

    settings = get_settings()
    target_tz = ZoneInfo(settings.default_timezone)
    placeholder_recipient = (
        settings.google_api_user_email or settings.smtp_user or "recipient@example.com"
    )
    ics_text = _build_plan_calendar(
        plan,
        organizer_email=settings.google_api_user_email or settings.smtp_user,
        recipient_email=placeholder_recipient,
        event_tz=target_tz,
    )
    buffer = io.BytesIO(ics_text.encode("utf-8"))
    return Response(
        content=buffer.getvalue(),
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=plan-{plan_id}.ics"},
    )


@router.post("/study/summarize", response_model=SummarizeResponse, tags=["study"])
async def summarize_content(
    payload: SummarizeRequest,
    request: Request,
    service: SummaryService = Depends(get_summary_service),
) -> SummarizeResponse:
    summary, fallback_used, truncated = await service.summarize(
        payload.text, payload.url, payload.user_request or "auto"
    )
    if fallback_used:
        request.state.fallback_used = True
    return SummarizeResponse(summary=summary, fallback_used=fallback_used, truncated=truncated)


@router.post("/study/quiz", response_model=QuizResponse, tags=["study"])
async def generate_quiz(
    payload: QuizRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    items, duplicate_rate, fallback_used, created_new = await service.get_or_create_quiz(
        payload.notes, session
    )
    await session.commit()
    if fallback_used:
        request.state.fallback_used = True
    return QuizResponse(items=items, duplicate_stem_rate=duplicate_rate, fallback_used=fallback_used)
