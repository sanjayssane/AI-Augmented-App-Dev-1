"""Examiner API routers."""

from app.api.v1.examiner.questions import router as questions_router
from app.api.v1.examiner.sessions import router as sessions_router
from app.api.v1.examiner.settings import router as settings_router
from app.api.v1.examiner.users import router as users_router

__all__ = ["questions_router", "sessions_router", "settings_router", "users_router"]
