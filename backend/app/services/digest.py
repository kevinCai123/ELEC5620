from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import DigestDeliveryLog, UserPreference
from app.schemas.emails import EmailSummary
from app.schemas.prefs import DigestPreviewResponse, DigestPreviewSection
from app.schemas.travel import TravelAdviceResponse
from app.services.email_summary import EmailService
from app.services.travel import TravelService
from app.utils.time import utc_now

_SETTINGS = get_settings()
_DEFAULT_TZ = ZoneInfo(_SETTINGS.default_timezone)


class DigestService:
    def __init__(self, email_service: EmailService, travel_service: TravelService) -> None:
        self._email_service = email_service
        self._travel_service = travel_service

    async def run_digest_cycle(self, session: AsyncSession) -> None:
        now_local = utc_now().astimezone(_DEFAULT_TZ)
        preferences = (await session.execute(select(UserPreference))).scalars().all()
        for pref in preferences:
            if not pref.digest_enabled or not pref.digest_time:
                continue
            scheduled_hour, scheduled_minute = map(int, pref.digest_time.split(":"))
            if not self._is_due(now_local, scheduled_hour, scheduled_minute, pref.timezone):
                continue
            if await self._already_delivered_today(session, pref.user_id, now_local.date()):
                continue
            await self._generate_and_store_digest(session, pref)

    async def _already_delivered_today(
        self, session: AsyncSession, user_id: str, date_value: date
    ) -> bool:
        stmt = (
            select(func.count(DigestDeliveryLog.id))
            .where(DigestDeliveryLog.user_id == user_id)
            .where(func.date(DigestDeliveryLog.delivered_at) == date_value.isoformat())
        )
        count = await session.scalar(stmt)
        return bool(count and count > 0)

    def _is_due(self, now_local: datetime, hour: int, minute: int, timezone: str) -> bool:
        tz = ZoneInfo(timezone)
        now_tz = now_local.astimezone(tz)
        return now_tz.hour == hour and now_tz.minute == minute

    async def _generate_and_store_digest(self, session: AsyncSession, pref: UserPreference) -> None:
        emails, email_fallback = await self._email_service.get_top_emails(5)
        travel = await self._travel_service.advise("UNSW Sydney", utc_now().astimezone(ZoneInfo(pref.timezone)))
        sections = self._compose_sections(emails, travel)
        payload = DigestPreviewResponse(generated_at=utc_now(), sections=sections)
        log = DigestDeliveryLog(
            user_id=pref.user_id,
            delivered_at=utc_now(),
            channel="preview",
            status="generated",
            content=json.dumps(payload.model_dump())
        )
        session.add(log)
        await session.flush()

    def _compose_sections(
        self, emails: list[EmailSummary], travel: TravelAdviceResponse
    ) -> list[DigestPreviewSection]:
        email_items = [f"{email.subject} — {email.summary}" for email in emails]
        travel_items = [travel.recommendation, f"Leave at {travel.leave_time.isoformat()}", f"Bring: {', '.join(travel.bring_items)}"]
        return [
            DigestPreviewSection(heading="Top Unread Emails", items=email_items or ["No unread emails"]),
            DigestPreviewSection(heading="Travel Advice", items=travel_items),
        ]

    async def latest_preview(self, session: AsyncSession) -> DigestPreviewResponse | None:
        stmt = select(DigestDeliveryLog).order_by(DigestDeliveryLog.delivered_at.desc()).limit(1)
        log = await session.scalar(stmt)
        if not log:
            return None
        data = json.loads(log.content)
        return DigestPreviewResponse.model_validate(data)


__all__ = ["DigestService"]
