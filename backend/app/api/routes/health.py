from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    return HealthResponse()
