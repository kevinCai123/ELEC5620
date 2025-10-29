from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_travel_service
from app.schemas.travel import TravelAdviceRequest, TravelAdviceResponse
from app.services.travel import TravelService

router = APIRouter()


@router.post("/travel/advise", response_model=TravelAdviceResponse, tags=["travel"])
async def travel_advise(
    payload: TravelAdviceRequest,
    request: Request,
    service: TravelService = Depends(get_travel_service),
) -> TravelAdviceResponse:
    advice = await service.advise(payload.location, payload.event_time)
    if advice.fallback_used:
        request.state.fallback_used = True
    return advice
