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


# ── Site Settings ─────────────────────────────────────────────────────────────

@router.get("/settings")
def get_site_settings(admin: Agent = Depends(require_permission("manage_settings"))):
    return {s.key: s.value for s in Setting.select()}


@router.put("/settings")
def update_site_settings(req: AppSettingsUpdate, admin: Agent = Depends(require_permission("manage_settings"))):
    data: Dict[str, Any] = {}
    if req.site_name is not None:
        data["site_name"] = req.site_name
    if req.widget_color is not None:
        data["widget_color"] = req.widget_color
    if req.welcome_message is not None:
        data["welcome_message"] = req.welcome_message
    if req.offline_message is not None:
        data["offline_message"] = req.offline_message
    if req.proactive_delay_seconds is not None:
        data["proactive_delay_seconds"] = str(req.proactive_delay_seconds)
    if req.notification_sound is not None:
        data["notification_sound"] = "true" if req.notification_sound else "false"
    if req.widget_width is not None:
        # 280–560 px arası sınırla
        data["widget_width"] = str(max(280, min(560, req.widget_width)))
    if req.proactive_bubbles is not None:
        data["proactive_bubbles"] = req.proactive_bubbles
    if req.widget_position is not None:
        data["widget_position"] = "left" if req.widget_position == "left" else "right"
    if req.language is not None:
        data["language"] = req.language if req.language in ("en", "tr") else "en"
    if req.widget_icon is not None:
        data["widget_icon"] = req.widget_icon[:8]
    if req.widget_radius is not None:
        data["widget_radius"] = str(max(0, min(28, req.widget_radius)))
    if req.widget_texts is not None:
        data["widget_texts"] = req.widget_texts
    if req.bubble_dismiss_days is not None:
        data["bubble_dismiss_days"] = str(max(0, req.bubble_dismiss_days))
    for key, value in data.items():
        (Setting.insert(key=key, value=str(value), updated_at=datetime.utcnow())
         .on_conflict(conflict_target=[Setting.key],
                      update={Setting.value: str(value), Setting.updated_at: datetime.utcnow()})
         .execute())
    from ...settings_cache import invalidate as _invalidate_settings
    _invalidate_settings()
    return {"ok": True}


# ── Canned Responses ──────────────────────────────────────────────────────────

@router.get("/canned")
def list_canned(agent: Agent = Depends(get_current_agent)):
    return [
        {
            "id": c.id,
            "title": c.title,
            "content": c.content,
            "shortcut": c.shortcut,
        }
        for c in CannedResponse.select().order_by(CannedResponse.title)
    ]


@router.post("/canned")
def create_canned(req: CannedCreate, agent: Agent = Depends(get_current_agent)):
    c = CannedResponse.create(
        title=req.title,
        content=req.content,
        shortcut=req.shortcut,
        created_by=agent,
    )
    return {"id": c.id, "title": c.title}


@router.delete("/canned/{canned_id}")
def delete_canned(canned_id: int, agent: Agent = Depends(get_current_agent)):
    CannedResponse.delete().where(CannedResponse.id == canned_id).execute()
    return {"ok": True}


# ── Tags ──────────────────────────────────────────────────────────────────────

@router.get("/tags")
def list_tags(agent: Agent = Depends(get_current_agent)):
    return [
        {"id": t.id, "name": t.name, "color": t.color, "created_at": t.created_at.isoformat()}
        for t in Tag.select().order_by(Tag.name)
    ]


@router.post("/tags")
def create_tag(req: TagCreate, agent: Agent = Depends(require_permission("manage_tags"))):
    if Tag.get_or_none(Tag.name == req.name):
        raise HTTPException(400, "Bu isimde etiket zaten var")
    t = Tag.create(name=req.name, color=req.color)
    return {"id": t.id, "name": t.name, "color": t.color}


@router.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, agent: Agent = Depends(require_permission("manage_tags"))):
    Tag.delete().where(Tag.id == tag_id).execute()
    return {"ok": True}


# ── Work Schedule ─────────────────────────────────────────────────────────────

@router.get("/schedule/{agent_id}")
def get_schedule(agent_id: int, agent: Agent = Depends(get_current_agent)):
    target = Agent.get_or_none(Agent.id == agent_id)
    if not target:
        raise HTTPException(404, "Temsilci bulunamadı")
    sched, _ = WorkSchedule.get_or_create(agent=target)
    return {
        "agent_id": agent_id,
        "schedule_json": sched.schedule_json,
        "timezone": sched.timezone,
    }


@router.put("/schedule/{agent_id}")
def update_schedule(agent_id: int, req: ScheduleUpdate, agent: Agent = Depends(require_permission("manage_schedule"))):
    target = Agent.get_or_none(Agent.id == agent_id)
    if not target:
        raise HTTPException(404, "Temsilci bulunamadı")
    sched, _ = WorkSchedule.get_or_create(agent=target)
    WorkSchedule.update(
        schedule_json=req.schedule_json,
        timezone=req.timezone
    ).where(WorkSchedule.id == sched.id).execute()
    return {"ok": True}


# ── Webhooks ──────────────────────────────────────────────────────────────────

@router.get("/webhooks")
def list_webhooks(admin: Agent = Depends(require_permission("manage_webhooks"))):
    return [
        {"id": w.id, "name": w.name, "type": w.type, "url": w.url,
         "telegram_chat_id": w.telegram_chat_id, "events_json": w.events_json,
         "is_enabled": w.is_enabled, "created_at": w.created_at.isoformat()}
        for w in WebhookConfig.select().order_by(WebhookConfig.created_at)
    ]

@router.post("/webhooks")
def create_webhook(req: WebhookCreate, admin: Agent = Depends(require_permission("manage_webhooks"))):
    w = WebhookConfig.create(
        name=req.name, type=req.type, url=req.url,
        telegram_chat_id=req.telegram_chat_id, events_json=req.events_json,
        is_enabled=req.is_enabled,
    )
    _audit(admin.display_name or admin.username, "webhook_create", "webhook", w.id, f"{req.type}: {req.name}")
    return {"id": w.id, "name": w.name}

@router.patch("/webhooks/{webhook_id}")
def update_webhook(webhook_id: int, req: WebhookUpdate, admin: Agent = Depends(require_permission("manage_webhooks"))):
    w = WebhookConfig.get_or_none(WebhookConfig.id == webhook_id)
    if not w:
        raise HTTPException(404, "Webhook bulunamadı")
    updates = {}
    if req.name is not None: updates["name"] = req.name
    if req.url is not None: updates["url"] = req.url
    if req.telegram_chat_id is not None: updates["telegram_chat_id"] = req.telegram_chat_id
    if req.events_json is not None: updates["events_json"] = req.events_json
    if req.is_enabled is not None: updates["is_enabled"] = req.is_enabled
    if updates:
        WebhookConfig.update(**updates).where(WebhookConfig.id == webhook_id).execute()
    return {"ok": True}

@router.delete("/webhooks/{webhook_id}")
def delete_webhook(webhook_id: int, admin: Agent = Depends(require_permission("manage_webhooks"))):
    WebhookConfig.delete().where(WebhookConfig.id == webhook_id).execute()
    return {"ok": True}

@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: int, admin: Agent = Depends(require_permission("manage_webhooks"))):
    w = WebhookConfig.get_or_none(WebhookConfig.id == webhook_id)
    if not w:
        raise HTTPException(404, "Webhook bulunamadı")
    await fire_event("test", {"message": "Support Tawk test webhook", "webhook_id": webhook_id})
    return {"ok": True}


