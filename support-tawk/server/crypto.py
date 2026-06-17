"""
Field-level encryption for sensitive data at rest.

Chat messages, visitor names/emails and internal notes are encrypted in the
database with AES (via Fernet). The key is derived from DATA_ENCRYPTION_KEY
(or SECRET_KEY as a fallback) so that anyone who only copies the SQLite file
cannot read conversation contents.

Values are stored with an "enc:v1:" prefix. Reads transparently decrypt
prefixed values and pass through any legacy plaintext unchanged, so the
feature can be enabled on an existing database and migrated gradually.
"""
from __future__ import annotations
import base64
import hashlib
import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

_PREFIX = "enc:v1:"


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    # Prefer a dedicated data key; fall back to the JWT secret key.
    raw = os.environ.get("DATA_ENCRYPTION_KEY") or os.environ.get("SECRET_KEY") or ""
    if not raw:
        # Last resort: read from config (covers non-env deployments).
        try:
            from .config import config
            raw = config.server.secret_key or ""
        except Exception:
            raw = ""
    # Derive a stable 32-byte key regardless of the input length/format.
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(value: str) -> str:
    """Encrypt a string. Empty/None values are returned untouched so that
    default="" columns and equality checks stay clean."""
    if value is None or value == "":
        return value
    if isinstance(value, str) and value.startswith(_PREFIX):
        return value  # already encrypted, never double-encrypt
    token = _fernet().encrypt(value.encode("utf-8")).decode("ascii")
    return _PREFIX + token


def decrypt(value: str) -> str:
    """Decrypt a value produced by encrypt(). Legacy plaintext (no prefix)
    is returned as-is for backward compatibility."""
    if value is None or value == "":
        return value
    if not isinstance(value, str) or not value.startswith(_PREFIX):
        return value  # legacy plaintext
    token = value[len(_PREFIX):]
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken:
        # Wrong key or corrupted data — return the raw stored value rather
        # than crashing the whole request.
        return value


def is_encrypted(value: str) -> bool:
    return isinstance(value, str) and value.startswith(_PREFIX)
