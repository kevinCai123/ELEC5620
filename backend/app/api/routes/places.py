from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_places_service
from app.schemas.places import PlacesResponse
from app.services.places import PlacesService

router = APIRouter()


@router.get("/places", response_model=PlacesResponse, tags=["places"])
async def search_places(
    request: Request,
    q: str = Query(default="", min_length=0),
    session: AsyncSession = Depends(get_db_session),
    service: PlacesService = Depends(get_places_service),
) -> PlacesResponse:
    results, fallback_used, guidance = await service.search(q, session)
    await session.commit()
    if fallback_used:
        request.state.fallback_used = True
    return PlacesResponse(query=q, results=results, fallback_used=fallback_used, guidance=guidance)
