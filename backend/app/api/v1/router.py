"""Aggregates all v1 API routers."""

from fastapi import APIRouter

from app.api.v1 import auth, examinee, health
from app.api.v1.examiner import questions, sessions, settings, users

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["health"])
api_v1_router.include_router(auth.router, tags=["auth"])
api_v1_router.include_router(examinee.router, tags=["examinee"])
api_v1_router.include_router(questions.router, tags=["examiner-questions"])
api_v1_router.include_router(sessions.router, tags=["examiner-sessions"])
api_v1_router.include_router(users.router, tags=["examiner-users"])
api_v1_router.include_router(settings.router, tags=["examiner-settings"])
