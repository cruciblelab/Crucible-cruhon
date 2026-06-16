from __future__ import annotations
import csv
import io
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

try:
    import openpyxl
    _HAS_OPENPYXL = True
except ImportError:
    _HAS_OPENPYXL = False
from ...database import (
    Department, Agent, Conversation, Message, CannedResponse,
    Tag, ConversationTag, BlacklistedIP, BanAppeal, Rating, WorkSchedule, Bot, BotRule, Setting,
    Note, WebhookConfig, VisitorPageView, VisitorField, AuditLog, OfflineMessage,
    Form, FormField, FormSubmission,
)
from ... import bot_matcher
from ...webhook_sender import fire_event
from ...auth import (
    hash_password, verify_password, create_token,
    get_current_agent, require_admin, require_permission, verify_ws_token,
    agent_permissions, validate_password_strength, PERMISSIONS,
    check_login_rate, record_login_failure, reset_login_rate, _DUMMY_HASH,
)
from ...ws_manager import manager
from ...config import config
from ... import seclog

from ._base import router, _audit
from ._schemas import *  # noqa: F401,F403  (request models)


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/login")
def login(req: LoginRequest, request: Request):
    ip = seclog.client_ip(request)

    # App-level rate limit — checked before hitting the DB
    check_login_rate(ip, req.username)

    agent = Agent.get_or_none(Agent.username == req.username, Agent.is_active == True)

    # Always run bcrypt to prevent username enumeration via response time
    candidate_hash = agent.password_hash if agent else _DUMMY_HASH
    password_ok = verify_password(req.password, candidate_hash)

    if not agent or not password_ok:
        record_login_failure(ip, req.username)
        seclog.login_failed(ip, req.username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    reset_login_rate(ip, req.username)
    seclog.login_ok(ip, req.username)
    token = create_token(agent.id, agent.role)
    return {
        "token": token,
        "agent": {
            "id": agent.id,
            "username": agent.username,
            "display_name": agent.display_name,
            "role": agent.role,
            "permissions": sorted(agent_permissions(agent)),
        }
    }


@router.get("/me")
def get_me(agent: Agent = Depends(get_current_agent)):
    return {
        "id": agent.id,
        "username": agent.username,
        "display_name": agent.display_name,
        "role": agent.role,
        "permissions": sorted(agent_permissions(agent)),
    }


@router.get("/permissions")
def list_permissions(agent: Agent = Depends(get_current_agent)):
    return PERMISSIONS


# ── Agents (CRUD) ─────────────────────────────────────────────────────────────

@router.get("/agents")
def list_agents(agent: Agent = Depends(get_current_agent)):
    agents = Agent.select().order_by(Agent.created_at)
    return [
        {
            "id": a.id,
            "username": a.username,
            "display_name": a.display_name,
            "role": a.role,
            "permissions": sorted(agent_permissions(a)),
            "is_active": a.is_active,
            "is_online": a.id in manager.online_agents(),
            "created_at": a.created_at.isoformat(),
            "department_id": getattr(a, "department_id", None),
        }
        for a in agents
    ]


@router.post("/agents")
def create_agent(req: AgentCreate, admin: Agent = Depends(require_permission("manage_agents"))):
    if Agent.get_or_none(Agent.username == req.username):
        raise HTTPException(400, "This username is already taken")
    pw_err = validate_password_strength(req.password)
    if pw_err:
        raise HTTPException(400, pw_err)
    role = req.role if req.role in ("admin", "agent") else "agent"
    perms = req.permissions or []
    a = Agent.create(
        username=req.username,
        password_hash=hash_password(req.password),
        display_name=req.display_name or req.username,
        role=role,
        permissions=json.dumps(perms),
    )
    _audit(admin.display_name or admin.username, "create_agent", "agent", a.id, req.username)
    return {"id": a.id, "username": a.username, "role": a.role}


@router.patch("/agents/{agent_id}")
def update_agent(agent_id: int, req: AgentUpdate, admin: Agent = Depends(require_permission("manage_agents"))):
    a = Agent.get_or_none(Agent.id == agent_id)
    if not a:
        raise HTTPException(404, "User not found")
    updates = {}
    if req.display_name is not None:
        updates["display_name"] = req.display_name
    if req.role is not None and req.role in ("admin", "agent"):
        updates["role"] = req.role
    if req.is_active is not None:
        updates["is_active"] = req.is_active
    if req.password is not None:
        pw_err = validate_password_strength(req.password)
        if pw_err:
            raise HTTPException(400, pw_err)
        updates["password_hash"] = hash_password(req.password)
    if req.department_id is not None:
        updates["department_id"] = req.department_id if req.department_id > 0 else None
    if req.permissions is not None:
        updates["permissions"] = json.dumps(req.permissions)
    if updates:
        Agent.update(**updates).where(Agent.id == agent_id).execute()
    _audit(admin.display_name or admin.username, "update_agent", "agent", agent_id, a.username)
    return {"ok": True}


@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: int, admin: Agent = Depends(require_permission("manage_agents"))):
    _audit(admin.display_name or admin.username, "delete_agent", "agent", agent_id)
    Agent.delete().where(Agent.id == agent_id).execute()
    return {"ok": True}


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile")
def get_profile(agent: Agent = Depends(get_current_agent)):
    return {
        "id": agent.id,
        "username": agent.username,
        "display_name": agent.display_name,
        "role": agent.role,
        "avatar_color": getattr(agent, "avatar_color", "#6366f1"),
    }


@router.patch("/profile")
def update_profile(req: ProfileUpdate, agent: Agent = Depends(get_current_agent)):
    updates: dict = {}
    if req.display_name is not None:
        updates["display_name"] = req.display_name
    if req.password is not None:
        pw_err = validate_password_strength(req.password)
        if pw_err:
            raise HTTPException(400, pw_err)
        updates["password_hash"] = hash_password(req.password)
    if req.avatar_color is not None:
        updates["avatar_color"] = req.avatar_color
    if updates:
        Agent.update(**updates).where(Agent.id == agent.id).execute()
    return {"ok": True}


