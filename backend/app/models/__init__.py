"""
SQLAlchemy ORM models (Phase 1).

Declarative Base and entity models per docs/MCQ_Platform_ERD.md.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """ORM metadata base — models attach in Phase 1."""
