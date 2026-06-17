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


# ── Agent WebSocket (real-time panel) ─────────────────────────────────────────

@router.websocket("/ws/{token}")
async def agent_ws(ws: WebSocket, token: str):
    agent = verify_ws_token(token)
    if not agent:
        await ws.close(code=4001)
        return

    await manager.connect_agent(agent.id, ws)
    Agent.update(is_online=True).where(Agent.id == agent.id).execute()
    await manager.broadcast_to_agents({"type": "agent_online", "agent_id": agent.id})

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            action = data.get("action")

            if action == "watch":
                manager.watch(agent.id, int(data["conversation_id"]))
                # Mark visitor messages as read + notify visitor
                conv_obj = Conversation.get_or_none(Conversation.id == int(data["conversation_id"]))
                if conv_obj:
                    updated = (Message.update(is_read=True)
                               .where(Message.conversation == conv_obj, Message.sender_type == "visitor", Message.is_read == False)
                               .execute())
                    if updated > 0:
                        await manager.send_to_visitor(conv_obj.visitor_id, {"type": "messages_read"})
            elif action == "unwatch":
                manager.unwatch(agent.id, int(data["conversation_id"]))
            elif action == "typing":
                conv_id = int(data.get("conversation_id", 0))
                conv = Conversation.get_or_none(Conversation.id == conv_id)
                if conv:
                    await manager.send_to_visitor(conv.visitor_id, {
                        "type": "agent_typing",
                        "agent_name": agent.display_name or agent.username,
                    })

    except WebSocketDisconnect:
        manager.disconnect_agent(agent.id)
        Agent.update(is_online=False).where(Agent.id == agent.id).execute()
        await manager.broadcast_to_agents({"type": "agent_offline", "agent_id": agent.id})


