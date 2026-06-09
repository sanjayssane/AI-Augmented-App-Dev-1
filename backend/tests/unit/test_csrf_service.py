"""Unit tests for CsrfService token validation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.schemas.errors import CsrfValidationError
from app.services.csrf_service import CsrfService


def test_validate_token_accepts_session_bound_token() -> None:
    csrf_store = MagicMock()
    csrf_store.validate.return_value = False
    service = CsrfService(csrf_store=csrf_store)

    service.validate_token("session-token", expected_token="session-token")

    csrf_store.validate.assert_not_called()


def test_validate_token_rejects_mismatched_session_token() -> None:
    service = CsrfService(csrf_store=MagicMock())

    with pytest.raises(CsrfValidationError):
        service.validate_token("wrong-token", expected_token="session-token")


def test_validate_token_checks_store_for_bootstrap_tokens() -> None:
    csrf_store = MagicMock()
    csrf_store.validate.return_value = True
    service = CsrfService(csrf_store=csrf_store)

    service.validate_token("bootstrap-token")

    csrf_store.validate.assert_called_once_with("bootstrap-token")
