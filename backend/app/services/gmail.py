from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from email.message import EmailMessage
from typing import List, Optional

try:  # pragma: no cover - optional dependency import
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    _GMAIL_IMPORT_ERROR: Exception | None = None
except ImportError as exc:  # pragma: no cover - environment-specific
    build = None  # type: ignore[assignment]
    HttpError = Exception  # type: ignore
    Credentials = None  # type: ignore
    Request = None  # type: ignore
    _GMAIL_IMPORT_ERROR = exc

from app.core.config import Settings

logger = logging.getLogger(__name__)

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
TOKEN_URI = "https://oauth2.googleapis.com/token"


class GmailNotConfiguredError(RuntimeError):
    """Raised when Gmail credentials are missing."""


@dataclass
class GmailMessage:
    id: str
    subject: str
    sender: str
    body: str
    snippet: str
    thread_id: Optional[str] = None
    internal_date: Optional[int] = None

    @property
    def web_link(self) -> Optional[str]:
        if not self.thread_id:
            return None
        return f"https://mail.google.com/mail/u/0/#inbox/{self.thread_id}"


class GmailClient:
    """Thin wrapper around Gmail API for fetching recent messages."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        if _GMAIL_IMPORT_ERROR is not None:
            raise GmailNotConfiguredError(
                "Gmail dependencies are missing. Install google-api-python-client, google-auth, and google-auth-oauthlib."
            ) from _GMAIL_IMPORT_ERROR
        if not self._is_configured():
            raise GmailNotConfiguredError("Gmail credentials are not fully configured")
        self._user_id = settings.google_api_user_email or "me"

    def _is_configured(self) -> bool:
        return all(
            [
                self._settings.google_client_id,
                self._settings.google_client_secret,
                self._settings.google_refresh_token,
            ]
        )

    def _credentials(self, scopes: Optional[List[str]] = None) -> Credentials:
        scopes = scopes or [GMAIL_READONLY_SCOPE]
        creds = Credentials(
            token=None,
            refresh_token=self._settings.google_refresh_token,
            client_id=self._settings.google_client_id,
            client_secret=self._settings.google_client_secret,
            token_uri=TOKEN_URI,
            scopes=scopes,
        )
        creds.refresh(Request())
        return creds

    def fetch_recent_messages(self, max_results: int) -> List[GmailMessage]:
        """Fetch up to `max_results` recent inbox messages."""
        try:
            service = build("gmail", "v1", credentials=self._credentials(), cache_discovery=False)
            response = (
                service.users()
                .messages()
                .list(userId=self._user_id, maxResults=max_results, q="in:inbox")
                .execute()
            )
        except HttpError as exc:  # pragma: no cover - external dependency
            raise RuntimeError(f"Gmail API list call failed: {exc}") from exc

        message_refs = response.get("messages", []) or []
        messages: List[GmailMessage] = []
        for ref in message_refs:
            message = self._get_message(service, ref["id"])
            if message:
                messages.append(message)
        return messages

    def send_email(
        self,
        *,
        subject: str,
        body_text: str,
        to_email: str,
        attachments: Optional[List[tuple[str, str, bytes, Optional[dict[str, str]]]]] = None,
        calendar_alternative: Optional[tuple[str, Optional[dict[str, str]]]] = None,
    ) -> None:
        if not to_email:
            raise ValueError("Recipient email address is required")
        if build is None:
            raise GmailNotConfiguredError(
                "Gmail dependencies are missing. Install google-api-python-client, google-auth, and google-auth-oauthlib."
            )
        creds = self._credentials([GMAIL_SEND_SCOPE])
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)

        message = EmailMessage()
        from_email = self._settings.google_api_user_email or to_email
        message["To"] = to_email
        message["From"] = from_email
        message["Subject"] = subject
        message.set_content(body_text)

        if calendar_alternative:
            calendar_text, params = calendar_alternative
            message.add_alternative(
                calendar_text,
                subtype="calendar",
                params=params,
            )

        for filename, mime_type, data, extra_params in attachments or []:
            maintype, subtype = mime_type.split("/", 1)
            message.add_attachment(
                data,
                maintype=maintype,
                subtype=subtype,
                filename=filename,
                params=extra_params,
            )

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        try:
            service.users().messages().send(userId=self._user_id, body={"raw": raw_message}).execute()
        except HttpError as exc:  # pragma: no cover - external dependency
            raise RuntimeError(f"Gmail API send call failed: {exc}") from exc

    def _get_message(self, service, message_id: str) -> Optional[GmailMessage]:
        try:
            payload = (
                service.users()
                .messages()
                .get(
                    userId=self._user_id,
                    id=message_id,
                    format="full",
                    metadataHeaders=["Subject", "From"],
                )
                .execute()
            )
        except HttpError as exc:  # pragma: no cover - network error
            logger.warning("Failed to fetch Gmail message %s: %s", message_id, exc)
            return None

        headers = {h["name"].lower(): h["value"] for h in payload.get("payload", {}).get("headers", [])}
        subject = headers.get("subject", "(no subject)")
        sender = headers.get("from", "(unknown sender)")
        snippet = payload.get("snippet", "").strip()
        body = self._extract_plain_text(payload.get("payload")) or snippet

        return GmailMessage(
            id=payload.get("id", message_id),
            subject=subject,
            sender=sender,
            body=body,
            snippet=snippet,
            thread_id=payload.get("threadId"),
            internal_date=int(payload.get("internalDate", "0")) if payload.get("internalDate") else None,
        )

    def _extract_plain_text(self, node: Optional[dict]) -> Optional[str]:
        if not node:
            return None
        mime_type = node.get("mimeType", "")
        body_data = node.get("body", {}).get("data")
        if mime_type.startswith("text/plain") and body_data:
            return self._decode_body(body_data)
        for part in node.get("parts", []) or []:
            text = self._extract_plain_text(part)
            if text:
                return text
        if mime_type.startswith("text/html") and body_data:
            html_text = self._decode_body(body_data)
            return self._strip_html(html_text)
        return None

    @staticmethod
    def _decode_body(data: str) -> str:
        try:
            decoded = base64.urlsafe_b64decode(data.encode("utf-8"))
            return decoded.decode("utf-8", errors="replace")
        except Exception:  # pragma: no cover - defensive
            return ""

    @staticmethod
    def _strip_html(html: str) -> str:
        clean = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
        clean = re.sub(r"<[^>]+>", " ", clean)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()


__all__ = ["GmailClient", "GmailMessage", "GmailNotConfiguredError"]
