from __future__ import annotations

import base64
from email import message_from_bytes
from types import SimpleNamespace

import pytest

from app.services import gmail as gmail_module


class DummyCredentials:
    def __init__(self, *, token=None, refresh_token, client_id, client_secret, token_uri, scopes):  # noqa: PLR0913
        self.token = token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_uri = token_uri
        self.scopes = scopes
        self.valid = False

    def refresh(self, _request) -> None:
        self.valid = True


class DummyRequest:
    pass


class DummyHttpError(Exception):
    def __init__(self, status: int):
        self.resp = SimpleNamespace(status=status)


class DummyMessages:
    def __init__(self, sent_store: list[str]) -> None:
        self._sent_store = sent_store

    def send(self, *, userId: str, body: dict) -> "DummyMessages":
        # userId can be "me" or the actual email
        self._sent_store.append(body["raw"])
        return self

    def execute(self) -> None:  # pragma: no cover - nothing to do
        return None


class DummyService:
    def __init__(self, sent_store: list[str]) -> None:
        self._sent_store = sent_store

    def users(self) -> "DummyService":
        return self

    def messages(self) -> DummyMessages:
        return DummyMessages(self._sent_store)


@pytest.mark.asyncio
async def test_gmail_client_send_email_with_calendar(monkeypatch) -> None:
    sent_payloads: list[str] = []
    monkeypatch.setattr(gmail_module, "_GMAIL_IMPORT_ERROR", None, raising=False)
    monkeypatch.setattr(gmail_module, "Credentials", DummyCredentials)
    monkeypatch.setattr(gmail_module, "Request", DummyRequest)
    monkeypatch.setattr(gmail_module, "HttpError", DummyHttpError)
    monkeypatch.setattr(
        gmail_module,
        "build",
        lambda *args, **kwargs: DummyService(sent_payloads),
    )

    settings = SimpleNamespace(
        google_client_id="client",
        google_client_secret="secret",
        google_refresh_token="refresh",
        google_api_user_email="sender@example.com",
    )
    client = gmail_module.GmailClient(settings)

    client.send_email(
        subject="Plan Ready",
        body_text="See attached plan.",
        to_email="recipient@example.com",
        attachments=[
            ("plan.ics", "text/calendar", b"BEGIN:VCALENDAR", {"method": "REQUEST"})
        ],
        calendar_alternative=("BEGIN:VCALENDAR", {"method": "REQUEST"}),
    )

    assert sent_payloads, "Expected an encoded message to be sent"
    raw_bytes = base64.urlsafe_b64decode(sent_payloads[0].encode("utf-8"))
    message = message_from_bytes(raw_bytes)

    assert message["Subject"] == "Plan Ready"
    assert message["From"] == "sender@example.com"
    assert message["To"] == "recipient@example.com"

    calendar_parts = [
        part
        for part in message.walk()
        if part.get_content_type() == "text/calendar"
    ]
    assert len(calendar_parts) == 2  # one inline alternative + attachment

    assert client._extract_plain_text(
        {
            "mimeType": "multipart/alternative",
            "parts": [
                {
                    "mimeType": "text/html",
                    "body": {
                        "data": base64.urlsafe_b64encode(b"<p>Hello <b>World</b></p>").decode(
                            "utf-8"
                        )
                    },
                }
            ],
        }
    ) == "Hello World"
