from __future__ import annotations

from zoneinfo import ZoneInfo

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app.api import api_router
from app.api.deps import get_digest_service
from app.core.config import get_settings
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.db.session import get_session
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("APScheduler missing from dependencies") from exc

settings = get_settings()
configure_logging()

def _before_send(event: dict, hint: dict | None) -> dict | None:
    request_data = event.get("request", {})
    if "data" in request_data:
        request_data["data"] = "[REDACTED]"
    event["request"] = request_data
    return event


if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1, before_send=_before_send)

app = FastAPI(
    title="Study Companion API",
    version="0.1.0",
    description="Backend services for study companion",
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

if settings.sentry_dsn:
    app.add_middleware(SentryAsgiMiddleware)

scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.default_timezone))


@app.on_event("startup")
async def on_startup() -> None:
    if not scheduler.running:
        scheduler.start()
    scheduler.add_job(run_digest_job, "interval", minutes=1, id="digest_job", replace_existing=True)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown()


async def run_digest_job() -> None:
    digest_service = get_digest_service()
    async with get_session() as session:
        await digest_service.run_digest_cycle(session)
        await session.commit()


app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"message": "Study Companion API"}
