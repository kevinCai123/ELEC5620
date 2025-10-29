from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_email_service
from app.schemas.emails import TopEmailsResponse
from app.services.email_summary import EmailService

router = APIRouter()


@router.get("/emails/top", response_model=TopEmailsResponse, tags=["emails"])
async def get_top_emails(
    request: Request,
    n: int = Query(default=5, ge=1, le=50),
    service: EmailService = Depends(get_email_service),
) -> TopEmailsResponse:
    emails, fallback_used = await service.get_top_emails(n)
    if fallback_used:
        request.state.fallback_used = True
    return TopEmailsResponse(emails=emails, fallback_used=fallback_used)
