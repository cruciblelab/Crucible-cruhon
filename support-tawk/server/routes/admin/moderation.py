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


# ── IP Blacklist ──────────────────────────────────────────────────────────────

@router.get("/blacklist")
def list_blacklist(agent: Agent = Depends(get_current_agent)):
    return [
        {
            "id": b.id,
            "ip": b.ip,
            "kind": getattr(b, "kind", "ip"),
            "reason": b.reason,
            "blocked_by": b.blocked_by_id,
            "created_at": b.created_at.isoformat(),
        }
        for b in BlacklistedIP.select().order_by(BlacklistedIP.created_at.desc())
    ]


@router.post("/blacklist")
async def add_blacklist(req: BlacklistCreate, agent: Agent = Depends(require_permission("manage_blacklist"))):
    kind = req.kind if req.kind in ("ip", "visitor") else "ip"
    if BlacklistedIP.get_or_none(BlacklistedIP.ip == req.ip):
        raise HTTPException(400, "Already blocked")
    b = BlacklistedIP.create(ip=req.ip, reason=req.reason, blocked_by=agent, kind=kind)
    _audit(agent.display_name or agent.username, "blacklist_add", kind, b.id, req.ip)
    # Push ban event to currently connected visitor
    ban_msg = {"type": "banned", "reason": req.reason or ""}
    if kind == "visitor":
        await manager.send_to_visitor(req.ip, ban_msg)
    elif kind == "ip":
        vid = manager.find_visitor_by_ip(req.ip)
        if vid:
            await manager.send_to_visitor(vid, ban_msg)
    return {"id": b.id, "ip": b.ip, "kind": kind}


@router.delete("/blacklist/{bl_id}")
def remove_blacklist(bl_id: int, agent: Agent = Depends(require_permission("manage_blacklist"))):
    _audit(agent.display_name or agent.username, "blacklist_remove", "ip", bl_id)
    BlacklistedIP.delete().where(BlacklistedIP.id == bl_id).execute()
    return {"ok": True}


# ── Ban Appeals ───────────────────────────────────────────────────────────────

@router.get("/appeals")
def list_appeals(agent: Agent = Depends(require_permission("manage_blacklist"))):
    return [
        {
            "id": a.id,
            "ip": a.ip,
            "visitor_id": a.visitor_id,
            "message": a.message,
            "status": a.status,
            "created_at": a.created_at.isoformat(),
            "reviewed_by": a.reviewed_by_id,
            "reviewed_at": a.reviewed_at.isoformat() if a.reviewed_at else None,
        }
        for a in BanAppeal.select().order_by(BanAppeal.created_at.desc())
    ]


@router.get("/appeals/pending-count")
def appeals_pending_count(agent: Agent = Depends(get_current_agent)):
    count = BanAppeal.select().where(BanAppeal.status == "pending").count()
    return {"count": count}


@router.post("/appeals/{appeal_id}/accept")
async def accept_appeal(appeal_id: int, agent: Agent = Depends(require_permission("manage_blacklist"))):
    appeal = BanAppeal.get_or_none(BanAppeal.id == appeal_id)
    if not appeal:
        raise HTTPException(404, "Appeal not found")
    # Remove all matching bans for this visitor
    if appeal.ip:
        BlacklistedIP.delete().where(BlacklistedIP.ip == appeal.ip, BlacklistedIP.kind == "ip").execute()
    if appeal.visitor_id:
        BlacklistedIP.delete().where(BlacklistedIP.ip == appeal.visitor_id, BlacklistedIP.kind == "visitor").execute()
    BanAppeal.update(
        status="accepted",
        reviewed_by=agent,
        reviewed_at=datetime.utcnow(),
    ).where(BanAppeal.id == appeal_id).execute()
    _audit(agent.display_name or agent.username, "appeal_accept", "ban_appeal", appeal_id)
    # Notify the visitor if still connected
    if appeal.visitor_id:
        await manager.send_to_visitor(appeal.visitor_id, {"type": "ban_lifted"})
    return {"ok": True}


@router.post("/appeals/{appeal_id}/reject")
def reject_appeal(appeal_id: int, agent: Agent = Depends(require_permission("manage_blacklist"))):
    appeal = BanAppeal.get_or_none(BanAppeal.id == appeal_id)
    if not appeal:
        raise HTTPException(404, "Appeal not found")
    BanAppeal.update(
        status="rejected",
        reviewed_by=agent,
        reviewed_at=datetime.utcnow(),
    ).where(BanAppeal.id == appeal_id).execute()
    _audit(agent.display_name or agent.username, "appeal_reject", "ban_appeal", appeal_id)
    return {"ok": True}


# ── Audit Log ─────────────────────────────────────────────────────────────────

@router.get("/audit-log")
def get_audit_log(
    limit: int = 100,
    offset: int = 0,
    agent: Agent = Depends(require_permission("view_audit"))
):
    logs = (AuditLog.select()
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset))
    return [
        {"id": l.id, "agent_name": l.agent_name, "action": l.action,
         "target_type": l.target_type, "target_id": l.target_id,
         "details": l.details, "created_at": l.created_at.isoformat()}
        for l in logs
    ]


# ── Offline Messages ──────────────────────────────────────────────────────────

@router.get("/offline-messages")
def list_offline_messages(agent: Agent = Depends(get_current_agent)):
    msgs = OfflineMessage.select().order_by(OfflineMessage.created_at.desc()).limit(100)
    return [
        {"id": m.id, "visitor_name": m.visitor_name, "visitor_email": m.visitor_email,
         "message": m.message, "page_url": m.page_url, "is_read": m.is_read,
         "created_at": m.created_at.isoformat()}
        for m in msgs
    ]

@router.patch("/offline-messages/{msg_id}/read")
def mark_offline_read(msg_id: int, agent: Agent = Depends(get_current_agent)):
    OfflineMessage.update(is_read=True).where(OfflineMessage.id == msg_id).execute()
    return {"ok": True}


