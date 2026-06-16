from __future__ import annotations
import json
import time
import bcrypt
import jwt
from datetime import datetime, timedelta
from threading import Lock
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import config
from .database import Agent

_SECRET = config.server.secret_key
_HOURS = config.admin.session_hours
_bearer = HTTPBearer(auto_error=False)

PERMISSIONS = [
    {"key": "manage_agents",      "label": "Agent & Role Management",  "desc": "Add/remove agents, assign roles"},
    {"key": "manage_blacklist",   "label": "Blocklist Management",      "desc": "Block/unblock IPs and visitors"},
    {"key": "manage_departments", "label": "Department Management",     "desc": "Create and assign departments"},
    {"key": "manage_settings",    "label": "Site Settings",             "desc": "Widget, language, appearance"},
    {"key": "manage_forms",       "label": "Form Management",           "desc": "Create and edit forms"},
    {"key": "manage_botflow",     "label": "Bot Flows",                 "desc": "Manage automated bot flows"},
    {"key": "manage_tags",        "label": "Tag Management",            "desc": "Create and delete tags"},
    {"key": "manage_webhooks",    "label": "Webhook Management",        "desc": "Webhook and integration settings"},
    {"key": "manage_schedule",    "label": "Work Hours",                "desc": "Set agent work schedules"},
    {"key": "delete_data",        "label": "Data Deletion",             "desc": "Permanently delete visitor data"},
    {"key": "view_audit",         "label": "Audit Log",                 "desc": "View admin activity logs"},
    {"key": "export_data",        "label": "Data Export",               "desc": "Download CSV/Excel reports"},
]
PERMISSION_KEYS = {p["key"] for p in PERMISSIONS}


def agent_permissions(agent: Agent) -> set:
    if agent.role == "admin":
        return set(PERMISSION_KEYS)
    try:
        perms = json.loads(agent.permissions or "[]")
        if isinstance(perms, list):
            return {p for p in perms if p in PERMISSION_KEYS}
    except Exception:
        pass
    return set()


def has_permission(agent: Agent, perm: str) -> bool:
    return perm in agent_permissions(agent)


_COMMON_PASSWORDS = {
    "admin123", "password", "12345678", "qwerty123", "admin1234",
    "password1", "11111111", "123456789", "letmein1", "welcome1",
}


def validate_password_strength(plain: str) -> str | None:
    """Return an error message if the password is too weak, else None.
    Requires 8+ chars and at least two character classes."""
    if not plain or len(plain) < 8:
        return "Password must be at least 8 characters long"
    if plain.lower() in _COMMON_PASSWORDS:
        return "This password is too common, please choose a stronger one"
    classes = sum([
        any(c.islower() for c in plain),
        any(c.isupper() for c in plain),
        any(c.isdigit() for c in plain),
        any(not c.isalnum() for c in plain),
    ])
    if classes < 2:
        return "Password must include at least two of: lowercase, uppercase, digits, symbols"
    return None


# ── Login rate limiter ────────────────────────────────────────────────────────
# Sliding-window counter keyed on IP + username.
# After MAX_ATTEMPTS failures within WINDOW_SECONDS the key is locked for
# LOCKOUT_SECONDS; the counter resets automatically once that period expires.

_MAX_ATTEMPTS   = 5
_WINDOW_SECONDS = 600   # 10 min — window tracked for each attempt
_LOCKOUT_SECONDS = 900  # 15 min — lock duration after hitting the limit

_rl_store: dict[str, list[float]] = {}
_rl_lock = Lock()


def _rl_key(ip: str, username: str) -> str:
    return f"{ip}\x00{username.lower()}"


def check_login_rate(ip: str, username: str) -> None:
    """Raise HTTP 429 if this IP+username combo is currently locked out."""
    key = _rl_key(ip, username)
    now = time.monotonic()
    with _rl_lock:
        ts = [t for t in _rl_store.get(key, []) if now - t < _LOCKOUT_SECONDS]
        _rl_store[key] = ts
        if len(ts) >= _MAX_ATTEMPTS:
            retry_after = int(_LOCKOUT_SECONDS - (now - ts[0]))
            raise HTTPException(
                status_code=429,
                detail=f"Too many failed attempts. Try again in {retry_after // 60 + 1} minutes.",
                headers={"Retry-After": str(max(retry_after, 1))},
            )


def record_login_failure(ip: str, username: str) -> None:
    key = _rl_key(ip, username)
    now = time.monotonic()
    with _rl_lock:
        ts = [t for t in _rl_store.get(key, []) if now - t < _LOCKOUT_SECONDS]
        ts.append(now)
        _rl_store[key] = ts


def reset_login_rate(ip: str, username: str) -> None:
    key = _rl_key(ip, username)
    with _rl_lock:
        _rl_store.pop(key, None)


# Dummy hash used when username not found — keeps response time constant
# to prevent username enumeration via timing.
_DUMMY_HASH = bcrypt.hashpw(b"dummy", bcrypt.gensalt()).decode()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(agent_id: int, role: str) -> str:
    payload = {
        "sub": str(agent_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=_HOURS),
    }
    return jwt.encode(payload, _SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, _SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_agent(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> Agent:
    if not creds:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_token(creds.credentials)
    agent = Agent.get_or_none(Agent.id == int(payload["sub"]), Agent.is_active == True)
    if not agent:
        raise HTTPException(status_code=401, detail="User not found")
    return agent


def require_admin(agent: Agent = Depends(get_current_agent)) -> Agent:
    if agent.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return agent


def require_permission(perm: str):
    def _dep(agent: Agent = Depends(get_current_agent)) -> Agent:
        if not has_permission(agent, perm):
            raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
        return agent
    return _dep


def verify_ws_token(token: str) -> Agent | None:
    try:
        payload = decode_token(token)
        return Agent.get_or_none(Agent.id == int(payload["sub"]), Agent.is_active == True)
    except Exception:
        return None
