from fastapi import APIRouter

from . import code, digest, emails, health, places, prefs, study, travel

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(emails.router)
api_router.include_router(study.router)
api_router.include_router(travel.router)
api_router.include_router(places.router)
api_router.include_router(prefs.router)
api_router.include_router(digest.router)
api_router.include_router(code.router)

__all__ = ["api_router"]
