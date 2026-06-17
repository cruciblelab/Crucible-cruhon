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

from ._base import router
from ._schemas import *  # noqa: F401,F403  (request models)


# ── Bots ──────────────────────────────────────────────────────────────────────

def _bot_summary(b: Bot) -> dict:
    return {
        "id": b.id,
        "name": b.name,
        "is_enabled": b.is_enabled,
        "is_default": b.is_default,
        "greeting": b.greeting,
        "options_json": b.options_json,
        "similarity_threshold": b.similarity_threshold,
        "priority": b.priority,
        "rule_count": BotRule.select().where(BotRule.bot_id == b.id).count(),
        "created_at": b.created_at.isoformat(),
    }


def _bot_rule_dict(r: BotRule) -> dict:
    return {
        "id": r.id,
        "triggers_json": r.triggers_json,
        "reply": r.reply,
        "department_id": getattr(r, "department_id", None),
        "is_enabled": r.is_enabled,
    }


@router.get("/bots")
def list_bots(agent: Agent = Depends(get_current_agent)):
    return [_bot_summary(b) for b in Bot.select().order_by(Bot.priority.desc(), Bot.created_at.desc())]


@router.post("/bots")
def create_bot(req: BotCreate, agent: Agent = Depends(require_permission("manage_botflow"))):
    b = Bot.create(
        name=req.name,
        greeting=req.greeting,
        options_json=req.options_json,
        similarity_threshold=req.similarity_threshold,
        priority=req.priority,
    )
    bot_matcher.invalidate()
    return {"id": b.id, "name": b.name}


@router.patch("/bots/{bot_id}")
def update_bot(bot_id: int, req: BotUpdate, agent: Agent = Depends(require_permission("manage_botflow"))):
    b = Bot.get_or_none(Bot.id == bot_id)
    if not b:
        raise HTTPException(404, "Bot bulunamadı")
    updates: Dict[str, Any] = {}
    if req.name is not None: updates["name"] = req.name
    if req.is_enabled is not None: updates["is_enabled"] = req.is_enabled
    if req.greeting is not None: updates["greeting"] = req.greeting
    if req.options_json is not None: updates["options_json"] = req.options_json
    if req.similarity_threshold is not None: updates["similarity_threshold"] = req.similarity_threshold
    if req.priority is not None: updates["priority"] = req.priority
    if req.is_default is not None:
        if req.is_default:
            Bot.update(is_default=False).where(Bot.id != bot_id).execute()
        updates["is_default"] = req.is_default
    if updates:
        Bot.update(**updates).where(Bot.id == bot_id).execute()
    bot_matcher.invalidate()
    return {"ok": True}


@router.delete("/bots/{bot_id}")
def delete_bot(bot_id: int, agent: Agent = Depends(require_permission("manage_botflow"))):
    Bot.delete().where(Bot.id == bot_id).execute()
    bot_matcher.invalidate()
    return {"ok": True}


@router.get("/bots/{bot_id}/rules")
def list_bot_rules(bot_id: int, agent: Agent = Depends(get_current_agent)):
    rules = BotRule.select().where(BotRule.bot_id == bot_id).order_by(BotRule.id)
    return [_bot_rule_dict(r) for r in rules]


@router.post("/bots/{bot_id}/rules")
def add_bot_rule(bot_id: int, req: BotRuleCreate, agent: Agent = Depends(require_permission("manage_botflow"))):
    if not Bot.get_or_none(Bot.id == bot_id):
        raise HTTPException(404, "Bot bulunamadı")
    r = BotRule.create(
        bot_id=bot_id,
        triggers_json=req.triggers_json,
        reply=req.reply,
        department_id=req.department_id,
        is_enabled=req.is_enabled,
    )
    bot_matcher.invalidate()
    return {"id": r.id}


@router.patch("/bots/{bot_id}/rules/{rule_id}")
def update_bot_rule(bot_id: int, rule_id: int, req: BotRuleUpdate, agent: Agent = Depends(require_permission("manage_botflow"))):
    r = BotRule.get_or_none(BotRule.id == rule_id, BotRule.bot_id == bot_id)
    if not r:
        raise HTTPException(404, "Kural bulunamadı")
    updates: Dict[str, Any] = {}
    if req.triggers_json is not None: updates["triggers_json"] = req.triggers_json
    if req.reply is not None: updates["reply"] = req.reply
    if req.department_id is not None: updates["department_id"] = req.department_id
    if req.is_enabled is not None: updates["is_enabled"] = req.is_enabled
    if updates:
        BotRule.update(**updates).where(BotRule.id == rule_id).execute()
    bot_matcher.invalidate()
    return {"ok": True}


@router.delete("/bots/{bot_id}/rules/{rule_id}")
def delete_bot_rule(bot_id: int, rule_id: int, agent: Agent = Depends(require_permission("manage_botflow"))):
    BotRule.delete().where(BotRule.id == rule_id, BotRule.bot_id == bot_id).execute()
    bot_matcher.invalidate()
    return {"ok": True}


@router.get("/bot-settings")
def get_bot_settings(agent: Agent = Depends(require_permission("manage_botflow"))):
    s = Setting.get_or_none(Setting.key == "bot_default_threshold")
    return {"default_threshold": int(s.value) if s else bot_matcher.DEFAULT_THRESHOLD}


@router.put("/bot-settings")
def update_bot_settings(req: BotSettingsUpdate, agent: Agent = Depends(require_permission("manage_botflow"))):
    value = max(0, min(100, req.default_threshold))
    (Setting.insert(key="bot_default_threshold", value=str(value), updated_at=datetime.utcnow())
     .on_conflict(conflict_target=[Setting.key],
                  update={Setting.value: str(value), Setting.updated_at: datetime.utcnow()})
     .execute())
    from ...settings_cache import invalidate as _invalidate_settings
    _invalidate_settings()
    bot_matcher.invalidate()
    return {"ok": True}


