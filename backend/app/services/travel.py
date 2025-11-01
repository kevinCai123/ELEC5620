from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote_plus

import httpx

from app.core.config import get_settings
from app.schemas.travel import TravelAdviceResponse
from app.utils.metrics import emit_metric, time_metric

_SETTINGS = get_settings()


class TravelService:
    def __init__(self) -> None:
        self._api_key = _SETTINGS.openweather_api_key
        self._fallback_minutes = _SETTINGS.generic_travel_buffer_minutes
        self._default_location = _SETTINGS.default_weather_location

    async def advise(self, location: str, when: datetime) -> TravelAdviceResponse:
        fallback_used = False
        weather_summary: dict[str, Any] | None = None

        with time_metric("p95_latency_ms", feature="travel"):
            if self._api_key:
                try:
                    weather_summary = await self._fetch_weather(location)
                except Exception:  # noqa: BLE001
                    if location.strip().lower() != self._default_location.strip().lower():
                        try:
                            weather_summary = await self._fetch_weather(self._default_location)
                        except Exception:  # noqa: BLE001
                            fallback_used = True
                        else:
                            fallback_used = False
                    else:
                        fallback_used = True
            else:
                fallback_used = True

        bring_items = []
        if weather_summary and weather_summary.get("rain", 0) > 0.3:
            bring_items.append("umbrella")
        if weather_summary and weather_summary.get("temp_c", 20) < 16:
            bring_items.append("jacket")
        if not bring_items:
            bring_items.append("water bottle")

        buffer_minutes = weather_summary.get("buffer_minutes", self._fallback_minutes) if weather_summary else self._fallback_minutes
        leave_time = when - timedelta(minutes=buffer_minutes)
        if leave_time.tzinfo is None:
            leave_time = leave_time.replace(tzinfo=when.tzinfo)

        recommendation = self._compose_recommendation(buffer_minutes, bring_items, fallback_used)
        route_url = f"{_SETTINGS.google_maps_base_url}&destination={quote_plus(location)}"

        # Include weather data if available
        weather_data = None
        if weather_summary:
            weather_data = {
                "rain": weather_summary.get("rain", 0.0),
                "temp_c": weather_summary.get("temp_c", 20.0),
                "wind_speed": weather_summary.get("wind_speed", 0.0),
            }

        emit_metric("fallback_rate", 1.0 if fallback_used else 0.0, feature="travel")
        return TravelAdviceResponse(
            leave_time=leave_time,
            recommendation=recommendation,
            bring_items=bring_items,
            route_url=route_url,
            fallback_used=fallback_used,
            weather=weather_data,
        )

    async def _fetch_weather(self, location: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": location, "appid": self._api_key, "units": "metric"},
            )
            response.raise_for_status()
            payload = response.json()
            rain = 0.0
            if "rain" in payload and "1h" in payload["rain"]:
                rain = float(payload["rain"]["1h"]) / 10  # convert mm to probability hint
            temp_c = payload.get("main", {}).get("temp", 20.0)
            wind = payload.get("wind", {}).get("speed", 3.0)
            buffer_minutes = max(self._fallback_minutes, int(wind))
            return {"rain": min(rain, 1.0), "temp_c": temp_c, "wind_speed": wind, "buffer_minutes": buffer_minutes}

    def _compose_recommendation(self, buffer_minutes: int, items: list[str], fallback: bool) -> str:
        base = f"Leave about {buffer_minutes} minutes earlier to stay on schedule."
        extras = f" Bring {' and '.join(items)}." if items else ""
        if fallback:
            return base + extras + " Weather data limited; using generic guidance."
        return base + extras


__all__ = ["TravelService"]
