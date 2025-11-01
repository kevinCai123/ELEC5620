from __future__ import annotations
from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator
from app.schemas.common import BaseSchema


class TravelAdviceRequest(BaseSchema):
    location: str = Field(min_length=2)
    event_time: datetime = Field(alias="datetime")

    @field_validator("event_time")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("datetime must include timezone")
        return value


class WeatherInfo(BaseSchema):
    # Core
    temp_c: float
    feels_like_c: Optional[float] = None
    condition_text: Optional[str] = None
    condition_icon_url: Optional[str] = None

    # Precip & clouds
    rain: Optional[float] = None                # 0.0–1.0 precip probability (keep your existing semantic)
    precip_mm: Optional[float] = None
    precipitation_chance: Optional[float] = None  # 0–1 or 0–100 (UI handles both)
    cloud: Optional[int] = None                 # 0–100 %

    # Wind
    wind_speed: Optional[float] = None          # m/s
    wind_gust: Optional[float] = None           # m/s
    wind_dir: Optional[str] = None

    # Atmosphere
    humidity: Optional[int] = None              # %
    dew_point_c: Optional[float] = None
    pressure_hpa: Optional[float] = None
    visibility_km: Optional[float] = None
    uv_index: Optional[float] = None
    aqi: Optional[int] = None                   # US AQI 0–500
    thunder_risk: Optional[float] = None        # 0.0–1.0

    # Solar times (optional, ISO8601 with tz)
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None


class TravelAdviceResponse(BaseSchema):
    leave_time: datetime
    recommendation: str
    bring_items: list[str]
    route_url: str
    fallback_used: bool = False
    weather: Optional[WeatherInfo] = None
    notes: list[str] = []  # optional extra hints/warnings
