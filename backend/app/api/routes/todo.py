from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_todo_service
from app.schemas.todo import (
    TodoCreateRequest,
    TodoExtractRequest,
    TodoExtractResponse,
    TodoListResponse,
)
from app.services.todo import TodoService

router = APIRouter()


@router.post("/todo/extract", response_model=TodoExtractResponse, tags=["todo"])
async def extract_todos(
    payload: TodoExtractRequest,
    request: Request,
    service: TodoService = Depends(get_todo_service),
) -> TodoExtractResponse:
    drafts, fallback_used = await service.extract(payload.text)
    if fallback_used:
        request.state.fallback_used = True
    return TodoExtractResponse(drafts=drafts)


@router.post("/todo", response_model=TodoListResponse, tags=["todo"])
async def create_todos(
    payload: TodoCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    service: TodoService = Depends(get_todo_service),
) -> TodoListResponse:
    created = await service.create_tasks(payload.tasks, session)
    await session.commit()
    return TodoListResponse(todos=created)


@router.get("/todo", response_model=TodoListResponse, tags=["todo"])
async def list_todos(
    session: AsyncSession = Depends(get_db_session),
    service: TodoService = Depends(get_todo_service),
) -> TodoListResponse:
    todos = await service.list_tasks(session)
    return TodoListResponse(todos=todos)
