"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import app_error_handler, validation_error_handler
from app.api.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.schemas.errors import AppError

app = FastAPI(
    title="MCQ Online Test Platform API",
    version="0.1.0",
    description="Role-based examination system API (Phase 0 scaffold).",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

app.include_router(api_v1_router, prefix="/api/v1")
