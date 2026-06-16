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


# ── Departments ───────────────────────────────────────────────────────────────

def _dept_full(d: Department) -> dict:
    member_count = Agent.select().where(Agent.department_id == d.id).count()
    conv_count = Conversation.select().where(
        Conversation.department_id == d.id,
        Conversation.status != "closed"
    ).count()
    return {
        "id": d.id,
        "name": d.name,
        "description": d.description,
        "color": d.color,
        "icon": d.icon,
        "member_count": member_count,
        "open_conversations": conv_count,
        "created_at": d.created_at.isoformat(),
    }


@router.get("/departments")
def list_departments(agent: Agent = Depends(get_current_agent)):
    return [_dept_full(d) for d in Department.select().order_by(Department.name)]


@router.post("/departments")
def create_department(req: DepartmentCreate, admin: Agent = Depends(require_permission("manage_departments"))):
    if Department.get_or_none(Department.name == req.name):
        raise HTTPException(400, "Bu isimde departman zaten var")
    d = Department.create(name=req.name, description=req.description,
                          color=req.color, icon=req.icon)
    _audit(admin.display_name or admin.username, "create_department", "department", d.id, req.name)
    return _dept_full(d)


@router.patch("/departments/{dept_id}")
def update_department(dept_id: int, req: DepartmentUpdate, admin: Agent = Depends(require_permission("manage_departments"))):
    d = Department.get_or_none(Department.id == dept_id)
    if not d:
        raise HTTPException(404, "Departman bulunamadı")
    updates = {}
    if req.name is not None:
        updates["name"] = req.name
    if req.description is not None:
        updates["description"] = req.description
    if req.color is not None:
        updates["color"] = req.color
    if req.icon is not None:
        updates["icon"] = req.icon
    if updates:
        Department.update(**updates).where(Department.id == dept_id).execute()
    return {"ok": True}


@router.delete("/departments/{dept_id}")
def delete_department(dept_id: int, admin: Agent = Depends(require_permission("manage_departments"))):
    # Unlink agents and conversations first
    Agent.update(department_id=None).where(Agent.department_id == dept_id).execute()
    Conversation.update(department_id=None).where(Conversation.department_id == dept_id).execute()
    Department.delete().where(Department.id == dept_id).execute()
    _audit(admin.display_name or admin.username, "delete_department", "department", dept_id)
    return {"ok": True}


@router.get("/departments/{dept_id}/agents")
def list_dept_agents(dept_id: int, agent: Agent = Depends(get_current_agent)):
    members = Agent.select().where(Agent.department_id == dept_id, Agent.is_active == True)
    return [{"id": a.id, "username": a.username, "display_name": a.display_name,
             "role": a.role, "is_online": a.id in manager.online_agents()} for a in members]


@router.post("/departments/{dept_id}/agents/{agent_id}")
def add_agent_to_dept(dept_id: int, agent_id: int, admin: Agent = Depends(require_permission("manage_departments"))):
    d = Department.get_or_none(Department.id == dept_id)
    if not d:
        raise HTTPException(404, "Departman bulunamadı")
    a = Agent.get_or_none(Agent.id == agent_id)
    if not a:
        raise HTTPException(404, "Temsilci bulunamadı")
    Agent.update(department_id=dept_id).where(Agent.id == agent_id).execute()
    return {"ok": True}


@router.delete("/departments/{dept_id}/agents/{agent_id}")
def remove_agent_from_dept(dept_id: int, agent_id: int, admin: Agent = Depends(require_permission("manage_departments"))):
    Agent.update(department_id=None).where(Agent.id == agent_id, Agent.department_id == dept_id).execute()
    return {"ok": True}


