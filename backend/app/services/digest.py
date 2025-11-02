from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime
import re
import smtplib
from typing import Any
from zoneinfo import ZoneInfo

import dateparser
from rapidfuzz import fuzz

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import DigestDeliveryLog, UserPreference
from app.schemas.emails import EmailSummary
from app.schemas.prefs import DigestPreviewResponse, DigestPreviewSection
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
        # Get user's email - assuming user_id is email address
        user_email = pref.user_id
        
        # Send the digest via email
        success, message = await self.send_digest_email(user_email)
        
        # Log the delivery attempt
        log = DigestDeliveryLog(
            user_id=pref.user_id,
            delivered_at=utc_now(),
            channel="email" if success else "failed",
            status="sent" if success else "error",
            content=message
        )
        session.add(log)
        await session.flush()

    async def _compose_sections(
        self, emails: list[EmailSummary]
    ) -> list[DigestPreviewSection]:
        # Generate a comprehensive summary of all 18 emails and surface suggested next actions
        from app.services.llm import LLMService

        llm_service = LLMService()

        if not emails:
            digest_data = self._build_simple_digest([])
            sections = [
                DigestPreviewSection(
                    heading="Email Digest Overview",
                    items=[digest_data["overview"]] if digest_data["overview"] else ["No emails available."],
                ),
                DigestPreviewSection(
                    heading="Key Highlights",
                    items=digest_data["highlights"] or ["No highlights identified."],
                ),
                DigestPreviewSection(
                    heading="Action Items",
                    items=digest_data["action_items"] or ["No immediate action items identified."],
                ),
                DigestPreviewSection(
                    heading="Tasks & Deadlines",
                    items=digest_data["tasks_and_deadlines"]
                    or ["No specific deadlines detected. Check back when new emails arrive."],
                ),
            ]
            todo_suggestions = digest_data.get("todo_suggestions") or []
            if todo_suggestions:
                sections.append(
                    DigestPreviewSection(
                        heading="Suggested TODOs",
                        items=todo_suggestions,
                    )
                )
            return sections

        email_texts: list[str] = []
        llm_email_payloads: list[dict[str, Any]] = []
        for index, email in enumerate(emails, start=1):
            key_points = ", ".join(email.key_points[:2]) if email.key_points else ""
            email_text = (
                f"{index}. Subject: {email.subject}\n"
                f"   From: {email.sender}\n"
                f"   Category: {email.category}\n"
                f"   Summary: {email.summary}"
            )
            if key_points:
                email_text += f"\n   Key Points: {key_points}"
            email_texts.append(email_text)
            llm_email_payloads.append(
                {
                    "id": email.id,
                    "subject": email.subject,
                    "sender": email.sender,
                    "category": email.category,
                    "summary": email.summary,
                    "key_points": email.key_points,
                    "text": email_text,
                }
            )

        combined_text = "\n\n".join(email_texts)

        # Generate comprehensive digest using LLM (includes tasks & deadlines)
        digest_result = await llm_service.generate_email_digest_simple(combined_text)

        if digest_result.fallback_used:
            # Fallback: Just list email summaries
            email_items = [f"{email.subject} — {email.summary}" for email in emails]
            return [
                DigestPreviewSection(heading="Email Digest (18 Recent Emails)", items=email_items or ["No emails"])
            ]

        # Return LLM-generated digest
        digest_data = digest_result.data
        sections = [
            DigestPreviewSection(heading="Email Digest Overview", items=[digest_data.get("overview", "")]),
            DigestPreviewSection(heading="Key Highlights", items=digest_data.get("highlights", [])),
            DigestPreviewSection(heading="Action Items", items=digest_data.get("action_items", [])),
            DigestPreviewSection(
                heading="Tasks & Deadlines",
                items=digest_data.get("tasks_and_deadlines", ["No tasks with deadlines found"])
            ),
        ]
        return sections

    def _build_digest_sections(
        self,
        emails: list[EmailSummary],
        digest_data: dict[str, list[str] | str],
        todo_suggestions: list[str],
    ) -> list[DigestPreviewSection]:
        overview_text = (
            digest_data.get("overview") or self._generate_overview_from_emails(emails)
        )
        overview_items = [overview_text] if overview_text else ["Summary unavailable."]

        priority_actions_source: list[str] = []
        priority_actions_source.extend(digest_data.get("action_items", []))  # type: ignore[assignment]
        priority_actions_source.extend(todo_suggestions)
        priority_actions = clamp_uniq(priority_actions_source, 5)
        if not priority_actions:
            priority_actions = ["No immediate action items identified."]

        deadlines_source: list[str] = digest_data.get("tasks_and_deadlines", [])  # type: ignore[arg-type]
        deadlines_items = self._build_deadline_items(deadlines_source, emails)
        if not deadlines_items:
            deadlines_items = ["No specific deadlines detected. Review highlighted emails for next steps."]

        threads_to_reply = self._identify_threads_requiring_reply(emails)

        topic_cards = self._build_topic_cards(emails)

        promotions_card = self._build_promotions_card(emails)
        security_items = self._detect_security_finance_alerts(emails)
        travel_items = self._detect_travel_events(emails)

        sections: list[DigestPreviewSection] = [
            DigestPreviewSection(heading="Overview", items=overview_items),
            DigestPreviewSection(heading="Priority Actions", items=priority_actions),
            DigestPreviewSection(heading="Deadlines & Dates", items=deadlines_items),
        ]

        if threads_to_reply:
            sections.append(
                DigestPreviewSection(heading="Threads To Reply", items=threads_to_reply)
            )

        if topic_cards:
            sections.append(
                DigestPreviewSection(heading="Grouped Topics", items=topic_cards)
            )

        clamped_highlights = clamp_uniq(digest_data.get("highlights", []), 6)  # type: ignore[arg-type]
        if clamped_highlights:
            sections.insert(
                1,
                DigestPreviewSection(
                    heading="Key Highlights",
                    items=clamped_highlights,
                ),
            )

        clamped_todos = clamp_uniq(todo_suggestions, 5)
        if clamped_todos:
            sections.append(
                DigestPreviewSection(heading="Suggested TODOs", items=clamped_todos)
            )

        if promotions_card:
            sections.append(
                DigestPreviewSection(
                    heading="Promotions & Newsletters", items=promotions_card
                )
            )

        if security_items:
            sections.append(
                DigestPreviewSection(
                    heading="Security & Finance Alerts", items=security_items
                )
            )

        if travel_items:
            sections.append(
                DigestPreviewSection(heading="Travel & Events", items=travel_items)
            )

        return sections

    async def generate_fresh_preview(self) -> DigestPreviewResponse:
        """Generate a fresh digest preview from the current 18 emails."""
        emails, _ = await self._email_service.get_top_emails(18)
        sections = await self._compose_sections(emails)
        return DigestPreviewResponse(generated_at=utc_now(), sections=sections)

    async def send_digest_email(self, recipient_email: str) -> tuple[bool, str]:
        """Send the current digest to the specified email address."""
        import asyncio
        from app.services.gmail import GmailClient, GmailNotConfiguredError
        
        try:
            # Generate fresh digest
            digest = await self.generate_fresh_preview()
            
            # Format digest as email body
            email_body = self._format_digest_for_email(digest)
            
            # Try Gmail API first
            try:
                gmail_client = GmailClient(_SETTINGS)
                await asyncio.to_thread(
                    gmail_client.send_email,
                    to_email=recipient_email,
                    subject=f"📧 Your Email Digest - {digest.generated_at.strftime('%B %d, %Y')}",
                    body_text=email_body,
                )
                return True, "Digest sent successfully via Gmail API"
            except (GmailNotConfiguredError, RuntimeError) as gmail_err:
                # Fallback to SMTP if Gmail fails
                if not all([_SETTINGS.smtp_host, _SETTINGS.smtp_user, _SETTINGS.smtp_pass]):
                    return False, f"Email sending failed: {str(gmail_err)}. SMTP not configured as fallback."
                
                from email.message import EmailMessage
                
                message = EmailMessage()
                message["Subject"] = f"📧 Your Email Digest - {digest.generated_at.strftime('%B %d, %Y')}"
                message["From"] = _SETTINGS.smtp_user
                message["To"] = recipient_email
                message.set_content(email_body)
                
                smtp_kwargs = {}
                if _SETTINGS.smtp_use_ssl:
                    smtp_class = smtplib.SMTP_SSL
                else:
                    smtp_class = smtplib.SMTP  # type: ignore[assignment]
                    if _SETTINGS.smtp_use_tls:
                        smtp_kwargs["timeout"] = 10
                
                await asyncio.to_thread(self._send_smtp, smtp_class, message, smtp_kwargs)
                return True, "Digest sent successfully via SMTP"
                
        except Exception as e:
            return False, f"Failed to send digest: {str(e)}"
    
    def _send_smtp(self, smtp_class, message, smtp_kwargs):
        """Helper to send email via SMTP."""
        with smtp_class(_SETTINGS.smtp_host, _SETTINGS.smtp_port or 587, **smtp_kwargs) as server:
            if _SETTINGS.smtp_use_tls and smtp_class == smtplib.SMTP:
                server.starttls()
            server.login(_SETTINGS.smtp_user, _SETTINGS.smtp_pass)
            server.send_message(message)
    
    def _format_digest_for_email(self, digest: DigestPreviewResponse) -> str:
        """Format the digest into a readable plain text email."""
        lines = [
            "="*60,
            "📧 YOUR EMAIL DIGEST",
            f"Generated: {digest.generated_at.strftime('%B %d, %Y at %I:%M %p')}",
            "="*60,
            "",
        ]
        
        for section in digest.sections:
            lines.append("")
            lines.append(f"📌 {section.heading.upper()}")
            lines.append("-" * 60)
            lines.append("")
            
            for idx, item in enumerate(section.items, 1):
                lines.append(f"  {idx}. {item}")
                lines.append("")
        
        lines.append("")
        lines.append("="*60)
        lines.append("This digest was generated by your Study Companion AI")
        lines.append("="*60)
        
        return "\n".join(lines)

    async def latest_preview(self, session: AsyncSession) -> DigestPreviewResponse | None:
        stmt = select(DigestDeliveryLog).order_by(DigestDeliveryLog.delivered_at.desc()).limit(1)
        log = await session.scalar(stmt)
        if not log:
            return None
        data = json.loads(log.content)
        return DigestPreviewResponse.model_validate(data)

    def _generate_overview_from_emails(self, emails: list[EmailSummary]) -> str:
        if not emails:
            return ""
        category_counts = Counter(
            (email.category or "other").lower().strip() for email in emails
        )
        most_common = ", ".join(
            cat.replace("_", " ").title() for cat, _ in category_counts.most_common(3)
        )
        promo_count = category_counts.get("promotional", 0)
        admin_count = category_counts.get("administrative", 0)
        academic_count = category_counts.get("academic", 0)
        return (
            f"{len(emails)} recent emails spanning {most_common or 'varied topics'}. "
            f"Academic: {academic_count}, Administrative: {admin_count}, Promotions: {promo_count}."
        )

    def _build_deadline_items(
        self, tasks: list[str], emails: list[EmailSummary]
    ) -> list[str]:
        deadlines: list[tuple[datetime, str]] = []
        seen: set[str] = set()
        settings = {
            "RETURN_AS_TIMEZONE_AWARE": False,
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": utc_now().replace(hour=9, minute=0, second=0, microsecond=0),
        }
        for raw in tasks:
            text = str(raw).strip()
            if not text or text.lower() in seen:
                continue
            parsed = dateparser.parse(text, settings=settings)
            if parsed:
                deadlines.append((parsed, text))
                seen.add(text.lower())

        if not deadlines:
            deadlines.extend(self._derive_deadlines_from_emails(emails))

        deadlines.sort(key=lambda item: item[0])
        formatted = [
            f"{dt.strftime('%Y-%m-%d')} — {entry}" for dt, entry in deadlines[:7]
        ]
        if formatted:
            return formatted

        # fall back to plain task strings capped at seven if we couldn't parse dates
        plain = clamp_uniq(tasks, 7)
        return plain

    def _derive_deadlines_from_emails(
        self, emails: list[EmailSummary]
    ) -> list[tuple[datetime, str]]:
        candidates: list[tuple[datetime, str]] = []
        settings = {
            "RETURN_AS_TIMEZONE_AWARE": False,
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": utc_now().replace(hour=9, minute=0, second=0, microsecond=0),
        }
        for email in emails:
            snippets = list(email.key_points or [])
            if email.summary:
                snippets.append(email.summary)
            for snippet in snippets:
                parsed = dateparser.parse(snippet, settings=settings)
                if parsed and any(
                    keyword in snippet.lower()
                    for keyword in ("due", "deadline", "expires", "register", "submit", "event")
                ):
                    candidates.append(
                        (
                            parsed,
                            f"{email.subject}: {snippet}",
                        )
                    )
        unique: dict[str, tuple[datetime, str]] = {}
        for dt, text in candidates:
            key = text.lower()
            if key not in unique or dt < unique[key][0]:
                unique[key] = (dt, text)
        return list(unique.values())

    def _identify_threads_requiring_reply(self, emails: list[EmailSummary]) -> list[str]:
        trigger_phrases = (
            "please confirm",
            "could you",
            "can you",
            "let us know",
            "awaiting",
            "need your response",
        )
        items: list[str] = []
        for email in emails:
            content_parts: list[str] = []
            if email.summary:
                content_parts.append(email.summary)
            content_parts.extend(email.key_points or [])
            combined = " ".join(content_parts)
            lower_combined = combined.lower()
            if not combined:
                continue
            suspects = any(phrase in lower_combined for phrase in trigger_phrases)
            if "?" in combined or suspects:
                sender = email.sender or "unknown sender"
                snippet = combined.split("\n")[0][:160]
                items.append(f"{email.subject} — reply likely needed (from {sender}): {snippet}")
        return clamp_uniq(items, 3)

    def _build_topic_cards(self, emails: list[EmailSummary]) -> list[str]:
        if not emails:
            return []
        items = [
            {
                "subject": email.subject or "(no subject)",
                "summary": email.summary or "",
                "category": email.category or "other",
                "key_points": list(email.key_points or []),
            }
            for email in emails
        ]
        groups = cluster_ids(items)
        cards: list[str] = []
        for group in groups:
            subjects = [items[idx]["subject"] for idx in group]
            representative = subjects[0]
            count = len(group)
            highlights: list[str] = []
            for idx in group:
                highlights.extend(items[idx]["key_points"][:1])
                if items[idx]["summary"]:
                    highlights.append(items[idx]["summary"][:120])
            highlight_text = clamp_uniq(highlights, 2)
            card = f"{representative} — {count} email{'s' if count > 1 else ''}"
            if highlight_text:
                card += f" | Highlights: {', '.join(highlight_text)}"
            cards.append(card)
        return clamp_uniq(cards, 6)

    def _build_promotions_card(self, emails: list[EmailSummary]) -> list[str]:
        promotional_emails = [
            email
            for email in emails
            if (email.category or "").lower() == "promotional"
            or any(
                keyword in (email.summary or "").lower()
                for keyword in ("sale", "offer", "discount", "deal", "promo", "unsubscribe")
            )
        ]
        if not promotional_emails:
            return []
        count = len(promotional_emails)
        senders = clamp_uniq(
            [email.sender or "Unknown sender" for email in promotional_emails], 4
        )
        summary = f"{count} promotional email{'s' if count != 1 else ''} ({', '.join(senders)})"
        suggestion = None
        if any(
            "unsubscribe" in (email.summary or "").lower()
            or any("unsubscribe" in kp.lower() for kp in (email.key_points or []))
            for email in promotional_emails
        ):
            suggestion = "Suggestion: Review unsubscribe options for recurring promotions."
        items = [summary]
        if suggestion:
            items.append(suggestion)
        return items

    def _detect_security_finance_alerts(self, emails: list[EmailSummary]) -> list[str]:
        keywords = (
            "password",
            "security",
            "login",
            "suspicious",
            "invoice",
            "billing",
            "payment",
            "transaction",
            "charge",
        )
        alerts: list[str] = []
        for email in emails:
            combined_parts = " ".join(
                filter(None, [email.summary, *(email.key_points or [])])
            )
            if any(keyword in combined_parts.lower() for keyword in keywords):
                snippet = combined_parts[:160] if combined_parts else ""
                alerts.append(f"{email.subject} — {snippet}")
        return clamp_uniq(alerts, 5)

    def _detect_travel_events(self, emails: list[EmailSummary]) -> list[str]:
        keywords = (
            "flight",
            "travel",
            "trip",
            "itinerary",
            "hotel",
            "conference",
            "event",
            "meeting",
            "venue",
        )
        travel_items: list[str] = []
        for email in emails:
            combined_parts = " ".join(
                filter(None, [email.summary, *(email.key_points or [])])
            )
            if any(keyword in combined_parts.lower() for keyword in keywords):
                travel_items.append(f"{email.subject} — {combined_parts[:160]}")
        return clamp_uniq(travel_items, 5)

    def _build_simple_digest(self, emails: list[EmailSummary]) -> dict[str, Any]:
        if not emails:
            return {
                "overview": "No recent emails available for digest generation.",
                "highlights": [],
                "action_items": [],
                "tasks_and_deadlines": [],
                "todo_suggestions": [],
            }

        categories = [email.category or "other" for email in emails]
        category_counts = Counter([category.lower() for category in categories if category])
        top_categories = [cat for cat, _ in category_counts.most_common(3)]
        category_phrase = ", ".join(cat.replace("_", " ").title() for cat in top_categories) if top_categories else "various categories"
        overview = f"{len(emails)} recent emails spanning {category_phrase}."

        # Highlights: prioritize emails with key points or longer summaries
        highlights: list[str] = []
        for email in emails:
            if email.summary:
                highlights.append(f"{email.subject} — {email.summary[:150]}")
            elif email.key_points:
                highlights.append(f"{email.subject} — {email.key_points[0]}")
            if len(highlights) >= 6:
                break

        # Action items: look for key points or summaries containing action verbs
        action_items: list[str] = []
        action_keywords = (
            "due",
            "deadline",
            "submit",
            "register",
            "update",
            "activate",
            "renew",
            "schedule",
            "book",
            "confirm",
            "purchase",
            "pay",
        )
        for email in emails:
            source_points = list(email.key_points or [])
            if not source_points and email.summary:
                source_points = [email.summary]
            for point in source_points:
                lower_point = point.lower()
                if any(keyword in lower_point for keyword in action_keywords):
                    action_items.append(f"{email.subject}: {point}")
                    if len(action_items) >= 5:
                        break
            if len(action_items) >= 5:
                break

        # Tasks & deadlines: extract items mentioning explicit dates or time-sensitive phrases
        tasks_and_deadlines: list[str] = []
        date_pattern = re.compile(
            r"(?:\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\b|\bNov(?:ember)?\s+\d{1,2}\b|\bDec(?:ember)?\s+\d{1,2}\b)",
            re.IGNORECASE,
        )
        for email in emails:
            candidates = list(email.key_points or [])
            if email.summary:
                candidates.append(email.summary)
            matched = False
            for candidate in candidates:
                if date_pattern.search(candidate) or "deadline" in candidate.lower() or "expires" in candidate.lower():
                    tasks_and_deadlines.append(f"{email.subject}: {candidate}")
                    matched = True
                    break
            if not matched and email.category and email.category.lower() in {"academic", "administrative"} and email.summary:
                tasks_and_deadlines.append(f"{email.subject}: {email.summary}")
            if len(tasks_and_deadlines) >= 7:
                break

        if not action_items:
            # Fall back to generic prompts if no explicit action items found
            selected = highlights[:3] if highlights else [email.subject for email in emails[:3]]
            action_items = [f"Review: {item}" for item in selected]

        if not tasks_and_deadlines:
            tasks_and_deadlines = ["No explicit deadlines detected; review highlighted emails for next steps."]

        return {
            "overview": overview,
            "highlights": highlights if highlights else [email.subject for email in emails[:5]],
            "action_items": action_items,
            "tasks_and_deadlines": tasks_and_deadlines,
            "todo_suggestions": self._build_todo_suggestions_from_emails(emails),
        }

    def _normalise_digest_data(self, data: Any) -> dict[str, list[str] | str]:
        if not isinstance(data, dict):
            try:
                data = dict(data)  # type: ignore[arg-type]
            except Exception:
                data = {}
        overview = str(data.get("overview") or "").strip()
        highlights = data.get("highlights") or []
        action_items = data.get("action_items") or []
        tasks_and_deadlines = data.get("tasks_and_deadlines") or []

        def _as_list(value: Any) -> list[str]:
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            if value:
                return [str(value)]
            return []

        return {
            "overview": overview,
            "highlights": _as_list(highlights),
            "action_items": _as_list(action_items),
            "tasks_and_deadlines": _as_list(tasks_and_deadlines),
        }

    def _format_llm_todo_suggestions(self, todos: Any) -> list[str]:
        suggestions: list[str] = []
        if not isinstance(todos, list):
            return suggestions
        for entry in todos:
            if hasattr(entry, "model_dump"):
                entry_dict = entry.model_dump()
            elif isinstance(entry, dict):
                entry_dict = entry
            else:
                continue
            task = str(entry_dict.get("task") or entry_dict.get("title") or "").strip()
            if not task:
                continue
            parts: list[str] = [task]
            due = entry_dict.get("due_date")
            if due:
                parts.append(f"Due: {due}")
            source = entry_dict.get("source_email")
            if source:
                parts.append(f"Email: {source}")
            suggestions.append(" — ".join(parts))
            if len(suggestions) >= 7:
                break
        return suggestions

    def _build_todo_suggestions_from_emails(self, emails: list[EmailSummary]) -> list[str]:
        suggestions: list[str] = []
        action_keywords = (
            "due",
            "deadline",
            "submit",
            "register",
            "update",
            "activate",
            "renew",
            "schedule",
            "book",
            "confirm",
            "purchase",
            "pay",
            "apply",
            "attend",
            "complete",
            "respond",
        )
        for email in emails:
            candidates = list(email.key_points or [])
            if email.summary:
                candidates.append(email.summary)
            for candidate in candidates:
                lower_candidate = candidate.lower()
                if any(keyword in lower_candidate for keyword in action_keywords):
                    suggestion = f"{email.subject}: {candidate}"
                    if suggestion not in suggestions:
                        suggestions.append(suggestion)
                    break
            if len(suggestions) >= 7:
                break
        if not suggestions:
            suggestions = [f"Review email: {email.subject}" for email in emails[:5]]
        return suggestions


__all__ = ["DigestService"]


def normalize_subject(subject: str) -> str:
    subject = re.sub(r"^(re|fwd):\s*", "", subject, flags=re.IGNORECASE)
    subject = re.sub(r"\[[^\]]+\]", "", subject)
    subject = re.sub(r"#\d+|\bID[:\s]*\d+\b", "", subject, flags=re.IGNORECASE)
    subject = re.sub(r"\s+", " ", subject)
    return subject.strip().lower()


def cluster_ids(items: list[dict[str, Any]], threshold: int = 85) -> list[list[int]]:
    groups: list[list[int]] = []
    for idx, item in enumerate(items):
        placed = False
        for group in groups:
            representative_subject = items[group[0]]["subject"]
            score = fuzz.ratio(
                normalize_subject(item["subject"]),
                normalize_subject(representative_subject),
            )
            if score >= threshold:
                group.append(idx)
                placed = True
                break
        if not placed:
            groups.append([idx])
    return groups


def clamp_uniq(values: list[Any], limit: int) -> list[str]:
    if limit <= 0:
        return []
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
        if len(result) >= limit:
            break
    return result
