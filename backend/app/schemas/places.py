from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema


class CampusPlace(BaseSchema):
    id: str
    name: str
    description: str | None = None
    aliases: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None


class PlacesResponse(BaseSchema):
    query: str
    results: List[CampusPlace]
    fallback_used: bool = False
    guidance: str | None = None
