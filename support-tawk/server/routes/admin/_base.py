"""Shared router instance and helpers for the admin route package."""
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

router = APIRouter(prefix="/api/admin")


def _audit(agent_name: str, action: str, target_type: str = "", target_id: int = None, details: str = ""):
    AuditLog.create(agent_name=agent_name, action=action, target_type=target_type, target_id=target_id, details=details)


def _conv_tags(conv_id: int) -> list:
    rows = (ConversationTag.select(ConversationTag, Tag)
            .join(Tag)
            .where(ConversationTag.conversation_id == conv_id))
    return [{"id": r.tag.id, "name": r.tag.name, "color": r.tag.color} for r in rows]


def _conv_rating(conv_id: int):
    r = Rating.get_or_none(Rating.conversation_id == conv_id)
    if r:
        return {"score": r.score, "comment": r.comment, "created_at": r.created_at.isoformat()}
    return None


def _dept_dict(conv: Conversation):
    dept_id = getattr(conv, "department_id", None)
    if not dept_id:
        return None
    d = Department.get_or_none(Department.id == dept_id)
    if not d:
        return None
    return {"id": d.id, "name": d.name, "color": d.color, "icon": d.icon}


def _conv_full(conv: Conversation) -> dict:
    msgs = list(Message.select().where(Message.conversation == conv).order_by(Message.created_at))
    assigned = None
    if conv.assigned_to_id:
        a = Agent.get_or_none(Agent.id == conv.assigned_to_id)
        if a:
            assigned = {"id": a.id, "username": a.username, "display_name": a.display_name}
    return {
        "id": conv.id,
        "visitor_id": conv.visitor_id,
        "visitor_name": conv.visitor_name,
        "visitor_email": conv.visitor_email,
        "status": conv.status,
        "assigned_to": assigned,
        "page_url": conv.page_url,
        "site_name": conv.site_name,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "visitor_online": manager.visitor_online(conv.visitor_id),
        "messages": [_msg_dict(m) for m in msgs],
        "unread_count": sum(1 for m in msgs if not m.is_read and m.sender_type == "visitor"),
        "tags": _conv_tags(conv.id),
        "rating": _conv_rating(conv.id),
        "ip_address": getattr(conv, "ip_address", ""),
        "user_agent": getattr(conv, "user_agent", ""),
        "country": getattr(conv, "country", ""),
        "city": getattr(conv, "city", ""),
        "language": getattr(conv, "language", ""),
        "priority": getattr(conv, "priority", "normal"),
        "department": _dept_dict(conv),
    }


def _msg_dict(msg: Message) -> dict:
    return {
        "id": msg.id,
        "sender_type": msg.sender_type,
        "sender_name": msg.sender_name,
        "content": msg.content,
        "file_url": msg.file_url,
        "file_name": msg.file_name,
        "file_size": msg.file_size,
        "is_read": msg.is_read,
        "created_at": msg.created_at.isoformat(),
    }


def _conv_summary(conv: Conversation) -> dict:
    last_msg = Message.select().where(Message.conversation == conv).order_by(Message.created_at.desc()).first()
    unread = Message.select().where(
        Message.conversation == conv,
        Message.sender_type == "visitor",
        Message.is_read == False
    ).count()
    assigned = None
    if conv.assigned_to_id:
        a = Agent.get_or_none(Agent.id == conv.assigned_to_id)
        if a:
            assigned = {"id": a.id, "username": a.username, "display_name": a.display_name}
    return {
        "id": conv.id,
        "visitor_id": conv.visitor_id,
        "visitor_name": conv.visitor_name,
        "visitor_email": conv.visitor_email,
        "status": conv.status,
        "assigned_to": assigned,
        "page_url": conv.page_url,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "visitor_online": manager.visitor_online(conv.visitor_id),
        "unread_count": unread,
        "last_message": _msg_dict(last_msg) if last_msg else None,
        "tags": _conv_tags(conv.id),
        "ip_address": getattr(conv, "ip_address", ""),
        "country": getattr(conv, "country", ""),
        "city": getattr(conv, "city", ""),
        "language": getattr(conv, "language", ""),
        "priority": getattr(conv, "priority", "normal"),
        "department": _dept_dict(conv),
    }

