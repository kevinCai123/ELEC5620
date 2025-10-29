from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.digest import DigestService
from app.services.email_summary import EmailService
from app.services.places import PlacesService
from app.services.quiz import QuizService
from app.services.summary import SummaryService
from app.services.todo import TodoService
from app.services.travel import TravelService


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with get_session() as session:
        yield session


@lru_cache
def get_email_service() -> EmailService:
    return EmailService()


@lru_cache
def get_summary_service() -> SummaryService:
    return SummaryService()


@lru_cache
def get_quiz_service() -> QuizService:
    return QuizService()


@lru_cache
def get_todo_service() -> TodoService:
    return TodoService()


@lru_cache
def get_travel_service() -> TravelService:
    return TravelService()


@lru_cache
def get_places_service() -> PlacesService:
    return PlacesService()


@lru_cache
def get_digest_service() -> DigestService:
    return DigestService(get_email_service(), get_travel_service())
