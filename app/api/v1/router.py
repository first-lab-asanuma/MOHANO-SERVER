from fastapi import APIRouter

from app.api.v1 import account, auth, availability, calls, chats, health, matching, profile

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(account.router, tags=["account"])
api_router.include_router(profile.router, tags=["profile"])
api_router.include_router(availability.router, tags=["availability"])
api_router.include_router(matching.router, tags=["matching"])
api_router.include_router(calls.router, tags=["calls"])
api_router.include_router(chats.router, tags=["chats"])
