from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    return datetime.now(tz=ZoneInfo("UTC"))


def to_timezone(dt: datetime, timezone: str) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(ZoneInfo(timezone))


__all__ = ["utc_now", "to_timezone"]
