from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_digest_service
from app.schemas.prefs import DigestPreviewResponse
from app.services.digest import DigestService

router = APIRouter()


@router.get("/digest/preview", response_model=DigestPreviewResponse, tags=["digest"])
async def digest_preview(
    session: AsyncSession = Depends(get_db_session),
    service: DigestService = Depends(get_digest_service),
) -> DigestPreviewResponse:
    preview = await service.latest_preview(session)
    if not preview:
        raise HTTPException(status_code=404, detail="No digest available")
    return preview
