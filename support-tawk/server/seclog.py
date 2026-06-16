"""
Security event logging.

Failed admin logins are written to a dedicated file in a stable, parseable
format so Fail2ban (or any log monitor) can ban abusive IPs. Message bodies
and other sensitive content are never written here.
"""
from __future__ import annotations
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_PATH = os.environ.get("SUPPORT_TAWK_SECURITY_LOG", "./data/security.log")

_logger = logging.getLogger("support_tawk.security")
_logger.setLevel(logging.INFO)
_logger.propagate = False

if not _logger.handlers:
    try:
        Path(_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(_LOG_PATH, maxBytes=2_000_000, backupCount=3)
    except Exception:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    _logger.addHandler(handler)


def _clean(value: str) -> str:
    # Keep the log line single-field and injection-safe.
    return "".join(c for c in str(value)[:64] if c.isalnum() or c in "._-@:")


def login_failed(ip: str, username: str) -> None:
    _logger.info("AUTH_FAIL ip=%s user=%s", _clean(ip or "unknown"), _clean(username or "?"))


def login_ok(ip: str, username: str) -> None:
    _logger.info("AUTH_OK ip=%s user=%s", _clean(ip or "unknown"), _clean(username or "?"))


def client_ip(request) -> str:
    """Real client IP, honouring the proxy's X-Forwarded-For header."""
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
