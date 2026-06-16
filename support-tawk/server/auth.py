from __future__ import annotations
import json
import bcrypt
import jwt
from datetime import datetime, timedelta
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
