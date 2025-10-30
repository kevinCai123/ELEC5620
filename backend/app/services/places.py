from __future__ import annotations

import json
from pathlib import Path
from rapidfuzz import fuzz
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SearchHistory
from app.schemas.places import CampusPlace
from app.utils.time import utc_now


class PlacesService:
    def __init__(self) -> None:
        data_path = Path(__file__).resolve().parent.parent / "data" / "places.json"
        with data_path.open("r", encoding="utf-8") as fh:
            self._places = [CampusPlace(**row) for row in json.load(fh)]

    async def search(self, query: str, session: AsyncSession | None = None) -> tuple[list[CampusPlace], bool, str | None]:
        if session:
            session.add(SearchHistory(query=query, created_at=utc_now()))

        if not query:
            return [], False, "Try searching by building name or tag."

        scored: list[tuple[CampusPlace, float]] = []
        for place in self._places:
            name_score = fuzz.partial_ratio(query, place.name)
            alias_score = max((fuzz.partial_ratio(query, alias) for alias in place.aliases), default=0)
            tag_score = max((fuzz.partial_ratio(query, tag) for tag in place.tags), default=0)
            total_score = (name_score * 0.6) + (alias_score * 0.3) + (tag_score * 0.1)
            scored.append((place, total_score))
        scored.sort(key=lambda item: item[1], reverse=True)
        results = [place for place, score in scored if score > 40][:5]
        fallback = len(results) == 0
        guidance = None if results else "No matches. Check spelling or search for nearby landmarks."
        return results, fallback, guidance


__all__ = ["PlacesService"]
