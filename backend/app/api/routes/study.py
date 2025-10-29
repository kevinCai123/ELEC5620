from __future__ import annotations

import io
from datetime import timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from icalendar import Calendar, Event

from app.api.deps import get_db_session, get_quiz_service, get_summary_service
from app.models import Plan, PlanItem
from app.schemas.quiz import QuizRequest, QuizResponse
from app.schemas.study import (
    StudyPlanCreateRequest,
    StudyPlanCreateResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from app.services.quiz import QuizService
from app.services.study import generate_plan_item_uid
from app.services.summary import SummaryService
from app.utils.time import utc_now

router = APIRouter()


@router.post("/study/plan", response_model=StudyPlanCreateResponse, tags=["study"])
async def create_study_plan(
    payload: StudyPlanCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> StudyPlanCreateResponse:
    plan = Plan(title=payload.title, created_by=payload.created_by, created_at=utc_now())
    session.add(plan)
    await session.flush()

    for item in payload.items:
        due_at = item.due_at
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=ZoneInfo("UTC"))
        due_at_utc = due_at.astimezone(ZoneInfo("UTC"))
        plan_item = PlanItem(plan_id=plan.id, title=item.title, due_at=due_at_utc, uid="pending")
        session.add(plan_item)
        await session.flush()
        plan_item.uid = generate_plan_item_uid(plan.id, plan_item.id)
    await session.commit()

    return StudyPlanCreateResponse(plan_id=plan.id)


@router.get("/study/plan/{plan_id}.ics", tags=["study"])
async def download_plan_ics(
    plan_id: int = Path(...),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    plan = await session.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    await session.refresh(plan, attribute_names=["items"])

    calendar = Calendar()
    calendar.add("prodid", "-//Study Companion//EN")
    calendar.add("version", "2.0")
    calendar.add("X-WR-TIMEZONE", "UTC")

    for item in plan.items:
        event = Event()
        event.add("summary", item.title)
        event.add("dtstart", item.due_at)
        event.add("dtend", item.due_at + timedelta(hours=1))
        event.add("uid", item.uid)
        event.add("description", plan.title)
        calendar.add_component(event)

    buffer = io.BytesIO(calendar.to_ical())
    return Response(
        content=buffer.getvalue(),
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=plan-{plan_id}.ics"},
    )


@router.post("/study/summarize", response_model=SummarizeResponse, tags=["study"])
async def summarize_content(
    payload: SummarizeRequest,
    request: Request,
    service: SummaryService = Depends(get_summary_service),
) -> SummarizeResponse:
    summary, fallback_used, truncated = await service.summarize(
        payload.text, payload.url, payload.user_request or "auto"
    )
    if fallback_used:
        request.state.fallback_used = True
    return SummarizeResponse(summary=summary, fallback_used=fallback_used, truncated=truncated)


@router.post("/study/quiz", response_model=QuizResponse, tags=["study"])
async def generate_quiz(
    payload: QuizRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    items, duplicate_rate, fallback_used, created_new = await service.get_or_create_quiz(
        payload.notes, session
    )
    await session.commit()
    if fallback_used:
        request.state.fallback_used = True
    return QuizResponse(items=items, duplicate_stem_rate=duplicate_rate, fallback_used=fallback_used)
