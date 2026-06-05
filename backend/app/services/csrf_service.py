"""CSRF token issuance and validation."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from app.repositories.redis.csrf_store import CsrfStore
from app.schemas.errors import CsrfValidationError


@dataclass
class CsrfIssueResult:
    token: str


class CsrfService:
    def __init__(self, csrf_store: CsrfStore) -> None:
        self._csrf_store = csrf_store

    def issue_token(self) -> CsrfIssueResult:
        token = self._csrf_store.issue_token()
        return CsrfIssueResult(token=token)

    def validate_token(self, submitted_token: str | None, expected_token: str | None = None) -> None:
        if not submitted_token:
            raise CsrfValidationError()
        if expected_token is not None and not secrets.compare_digest(submitted_token, expected_token):
            raise CsrfValidationError()
        if not self._csrf_store.validate(submitted_token):
            raise CsrfValidationError()
