"""
Tiny in-process cache for the Settings table.

The public /api/config endpoint is hit on every visitor page load, and it
reads all override settings. Those rows change rarely, so we cache them with
a short TTL and invalidate explicitly whenever the admin saves settings.
"""
from __future__ import annotations
import time
import threading

_TTL = 30.0  # seconds
_lock = threading.Lock()
_cache: dict | None = None
_expires_at: float = 0.0


def get_settings() -> dict:
    """Return {key: value} for all Setting rows, cached for _TTL seconds."""
    global _cache, _expires_at
    now = time.monotonic()
    with _lock:
        if _cache is not None and now < _expires_at:
            return _cache
    # Import here to avoid a circular import at module load time.
    from .database import Setting
    data = {s.key: s.value for s in Setting.select()}
    with _lock:
        _cache = data
        _expires_at = time.monotonic() + _TTL
    return data


def invalidate() -> None:
    """Drop the cache immediately (call after writing settings)."""
    global _cache, _expires_at
    with _lock:
        _cache = None
        _expires_at = 0.0
