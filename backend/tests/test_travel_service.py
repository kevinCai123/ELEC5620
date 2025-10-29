from __future__ import annotations

from datetime import datetime

import pytest
from zoneinfo import ZoneInfo

from app.services.travel import TravelService


@pytest.mark.asyncio
async def test_travel_advice_includes_recommendation() -> None:
    service = TravelService()
    when = datetime.now(tz=ZoneInfo("Australia/Sydney"))
    advice = await service.advise("UNSW Sydney", when)
    assert "Leave about" in advice.recommendation
    assert advice.route_url.startswith("https://www.google.com/maps/dir/")
    assert advice.bring_items, "Should suggest items to bring"
