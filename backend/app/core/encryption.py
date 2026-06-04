"""Field-level encryption helpers for examinee PII (Phase 1)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from functools import lru_cache

from app.core.config import settings


def _pepper() -> bytes:
    raw = os.environ.get("PRN_LOOKUP_PEPPER", settings.database_url)
    return raw.encode("utf-8")


@lru_cache
def _fernet_key() -> bytes:
    """Derive a Fernet-compatible key from ENCRYPTION_KEY or dev fallback."""
    raw = os.environ.get("ENCRYPTION_KEY", settings.database_url)
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def normalise_prn(prn: str) -> str:
    return prn.strip().upper()


def prn_lookup_hash(prn: str) -> str:
    """HMAC-SHA256 hex digest for duplicate PRN detection."""
    normalised = normalise_prn(prn)
    return hmac.new(_pepper(), normalised.encode("utf-8"), hashlib.sha256).hexdigest()


def encrypt_field(plaintext: str) -> str:
    """Encrypt a string for storage (Fernet)."""
    from cryptography.fernet import Fernet

    token = Fernet(_fernet_key()).encrypt(plaintext.encode("utf-8"))
    return token.decode("ascii")


def decrypt_field(ciphertext: str) -> str:
    """Decrypt a stored ciphertext field."""
    from cryptography.fernet import Fernet

    return Fernet(_fernet_key()).decrypt(ciphertext.encode("ascii")).decode("utf-8")
