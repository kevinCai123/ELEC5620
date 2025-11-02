"""Tests for app/utils/time.py - time utilities."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.utils.time import to_timezone, utc_now


def test_utc_now_returns_datetime_with_utc_timezone():
    """Test that utc_now returns a datetime with UTC timezone."""
    result = utc_now()
    
    assert isinstance(result, datetime)
    assert result.tzinfo == ZoneInfo("UTC")


def test_utc_now_returns_current_time():
    """Test that utc_now returns approximately current time."""
    before = datetime.now(tz=ZoneInfo("UTC"))
    result = utc_now()
    after = datetime.now(tz=ZoneInfo("UTC"))
    
    # Should be between before and after (within a few seconds)
    assert before <= result <= after


def test_to_timezone_converts_utc_to_target_timezone():
    """Test that to_timezone converts UTC datetime to target timezone."""
    utc_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
    
    # Convert to Sydney time (usually UTC+10 or UTC+11)
    sydney_dt = to_timezone(utc_dt, "Australia/Sydney")
    
    assert sydney_dt.tzinfo == ZoneInfo("Australia/Sydney")
    # Time should be different (ahead of UTC)
    assert sydney_dt.hour != utc_dt.hour or sydney_dt.day != utc_dt.day


def test_to_timezone_handles_naive_datetime():
    """Test that to_timezone handles naive (no timezone) datetime."""
    naive_dt = datetime(2025, 1, 1, 12, 0, 0)
    
    # Should assume UTC for naive datetime
    result = to_timezone(naive_dt, "America/New_York")
    
    assert result.tzinfo == ZoneInfo("America/New_York")


def test_to_timezone_converts_between_non_utc_timezones():
    """Test converting between non-UTC timezones."""
    ny_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("America/New_York"))
    
    # Convert to Tokyo time
    tokyo_dt = to_timezone(ny_dt, "Asia/Tokyo")
    
    assert tokyo_dt.tzinfo == ZoneInfo("Asia/Tokyo")
    # Tokyo is ahead of New York
    assert tokyo_dt.hour != ny_dt.hour or tokyo_dt.day != ny_dt.day


def test_to_timezone_preserves_datetime_value():
    """Test that to_timezone preserves the actual moment in time."""
    utc_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
    
    # Convert to different timezone
    sydney_dt = to_timezone(utc_dt, "Australia/Sydney")
    
    # Convert back to UTC
    back_to_utc = sydney_dt.astimezone(ZoneInfo("UTC"))
    
    # Should be the same moment in time
    assert back_to_utc == utc_dt


def test_to_timezone_handles_dst_transitions():
    """Test that to_timezone handles daylight saving time transitions."""
    # Use a date during DST
    summer_dt = datetime(2025, 7, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
    ny_summer = to_timezone(summer_dt, "America/New_York")
    
    # Use a date during standard time
    winter_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
    ny_winter = to_timezone(winter_dt, "America/New_York")
    
    # Both should have correct timezone
    assert ny_summer.tzinfo == ZoneInfo("America/New_York")
    assert ny_winter.tzinfo == ZoneInfo("America/New_York")
    
    # Offset from UTC should be different due to DST
    # (This tests that ZoneInfo is handling DST correctly)
    assert ny_summer.utcoffset() != ny_winter.utcoffset()

