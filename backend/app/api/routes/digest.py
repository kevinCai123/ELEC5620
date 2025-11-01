from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_digest_service
from app.schemas.prefs import DigestEmailRequest, DigestEmailResponse, DigestPreviewResponse
from app.services.digest import DigestService

router = APIRouter()


@router.get("/digest/preview", response_model=DigestPreviewResponse, tags=["digest"])
async def digest_preview(
    service: DigestService = Depends(get_digest_service),
) -> DigestPreviewResponse:
    """Generate a fresh digest from the current 18 emails with AI-powered comprehensive summary."""
    preview = await service.generate_fresh_preview()
    return preview


@router.post("/digest/send", response_model=DigestEmailResponse, tags=["digest"])
async def send_digest_email(
    payload: DigestEmailRequest,
    service: DigestService = Depends(get_digest_service),
) -> DigestEmailResponse:
    """Send the current digest to the specified email address."""
    success, message = await service.send_digest_email(payload.recipient_email)
    if not success:
        raise HTTPException(status_code=500, detail=message)
    return DigestEmailResponse(success=success, message=message)
