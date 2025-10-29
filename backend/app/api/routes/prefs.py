from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models import UserPreference
from app.schemas.prefs import DigestPreferenceRequest, DigestPreferenceResponse
from app.utils.time import utc_now

router = APIRouter()


@router.post("/prefs/digest", response_model=DigestPreferenceResponse, tags=["prefs"])
async def update_digest_preferences(
    payload: DigestPreferenceRequest,
    session: AsyncSession = Depends(get_db_session),
) -> DigestPreferenceResponse:
    preference = await session.get(UserPreference, payload.user_id)
    if preference:
        preference.digest_enabled = payload.digest_enabled
        preference.digest_time = payload.digest_time
        preference.timezone = payload.timezone
        preference.updated_at = utc_now()
    else:
        preference = UserPreference(
            user_id=payload.user_id,
            digest_enabled=payload.digest_enabled,
            digest_time=payload.digest_time,
            timezone=payload.timezone,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(preference)
    await session.commit()

    return DigestPreferenceResponse(
        user_id=preference.user_id,
        digest_enabled=preference.digest_enabled,
        digest_time=preference.digest_time,
        timezone=preference.timezone,
    )
