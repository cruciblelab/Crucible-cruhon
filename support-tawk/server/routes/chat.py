from __future__ import annotations
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from pydantic import BaseModel
from ..database import Department, Conversation, Message, Agent, BlacklistedIP, BanAppeal, Bot, Rating, WorkSchedule, Note, WebhookConfig, VisitorPageView, VisitorField, OfflineMessage
from ..webhook_sender import fire_event
from ..ws_manager import manager
from ..config import config
from ..ai_handler import handle_ai_reply
from .. import bot_matcher
from ..auth import verify_ws_token
from ..geoip import lookup as geo_lookup

router = APIRouter()


class RatingRequest(BaseModel):
    score: int
    comment: str = ""


def _msg_dict(msg: Message) -> dict:
    return {
        "id": msg.id,
        "sender_type": msg.sender_type,
        "sender_name": msg.sender_name,
        "content": msg.content,
        "file_url": msg.file_url,
        "file_name": msg.file_name,
        "created_at": msg.created_at.isoformat(),
    }


def _conv_dict(conv: Conversation) -> dict:
    return {
        "id": conv.id,
        "visitor_id": conv.visitor_id,
        "visitor_name": conv.visitor_name,
        "visitor_email": conv.visitor_email,
        "status": conv.status,
        "assigned_to": conv.assigned_to_id,
        "page_url": conv.page_url,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
    }


class OfflineMessageRequest(BaseModel):
    visitor_id: str = ""
    visitor_name: str = ""
    visitor_email: str = ""
    message: str
    page_url: str = ""


@router.post("/api/offline-message")
async def submit_offline_message(req: OfflineMessageRequest):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty")
    om = OfflineMessage.create(
        visitor_id=req.visitor_id,
        visitor_name=req.visitor_name,
        visitor_email=req.visitor_email,
        message=req.message.strip(),
        page_url=req.page_url,
    )
    asyncio.create_task(fire_event("offline_message", {
        "visitor_name": req.visitor_name,
        "visitor_email": req.visitor_email,
        "message": req.message.strip(),
        "page_url": req.page_url,
    }))
    await manager.broadcast_to_agents({
        "type": "offline_message",
        "offline_message": {
            "id": om.id,
            "visitor_name": req.visitor_name,
            "visitor_email": req.visitor_email,
            "message": req.message,
            "page_url": req.page_url,
            "created_at": om.created_at.isoformat(),
        }
    })
    return {"ok": True}


@router.post("/api/rating/{conv_id}")
async def submit_rating(conv_id: int, req: RatingRequest):
    conv = Conversation.get_or_none(Conversation.id == conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    if req.score < 1 or req.score > 5:
        raise HTTPException(400, "Rating must be between 1 and 5")
    Rating.insert(
        conversation=conv,
        score=req.score,
        comment=req.comment,
    ).on_conflict_replace().execute()
    return {"ok": True}


@router.get("/api/bot/greeting")
def get_bot_greeting():
    b = Bot.get_or_none(Bot.is_default == True, Bot.is_enabled == True)
    if not b:
        return None
    return {
        "id": b.id,
        "name": b.name,
        "greeting": b.greeting,
        "options": json.loads(b.options_json or "[]"),
    }


@router.get("/api/schedule/status")
def schedule_status():
    """Public: returns whether any agent is currently available based on work schedule."""
    now = datetime.utcnow()
    weekdays = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    current_day = weekdays[now.weekday()]
    current_time = now.strftime("%H:%M")
    schedules = WorkSchedule.select()
    for sched in schedules:
        try:
            data = json.loads(sched.schedule_json or "{}")
            day_data = data.get(current_day, {})
            if day_data.get("active") and day_data.get("start") and day_data.get("end"):
                if day_data["start"] <= current_time <= day_data["end"]:
                    return {"available": True}
        except Exception:
            continue
    agents_online = manager.agent_count() > 0
    return {"available": agents_online}


class BanAppealRequest(BaseModel):
    visitor_id: str
    message: str = ""


@router.post("/api/ban-appeal")
async def submit_ban_appeal(req: BanAppealRequest, request: Request):
    xff = request.headers.get("x-forwarded-for", "")
    client_ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else "unknown")

    ban = BlacklistedIP.get_or_none(
        ((BlacklistedIP.ip == client_ip) & (BlacklistedIP.kind == "ip")) |
        ((BlacklistedIP.ip == req.visitor_id) & (BlacklistedIP.kind == "visitor"))
    )
    if not ban:
        raise HTTPException(400, "No active ban found for this visitor.")

    existing = BanAppeal.get_or_none(
        (BanAppeal.ip == client_ip) | (BanAppeal.visitor_id == req.visitor_id),
        BanAppeal.status == "pending",
    )
    if existing:
        raise HTTPException(400, "An appeal is already pending review.")

    BanAppeal.create(
        ip=client_ip,
        visitor_id=req.visitor_id,
        message=req.message[:1000],
    )
    return {"ok": True}


@router.websocket("/ws/visitor/{visitor_id}")
async def visitor_ws(ws: WebSocket, visitor_id: str):
    # IP blacklist check
    client_ip = "unknown"
    if ws.client:
        client_ip = ws.client.host
    # Also check X-Forwarded-For
    forwarded_for = ws.headers.get("x-forwarded-for", "")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    ban = BlacklistedIP.get_or_none(
        ((BlacklistedIP.ip == client_ip) & (BlacklistedIP.kind == "ip")) |
        ((BlacklistedIP.ip == visitor_id) & (BlacklistedIP.kind == "visitor"))
    )
    if ban:
        await ws.accept()
        await ws.send_json({"type": "banned", "reason": ban.reason or ""})
        await ws.close(code=4403)
        return

    user_agent = ws.headers.get("user-agent", "")[:512]
    accept_lang = ws.headers.get("accept-language", "")
    language = accept_lang.split(",")[0].split(";")[0].strip()[:16] if accept_lang else ""

    await manager.connect_visitor(visitor_id, ws, ip=client_ip)
    conv = Conversation.get_or_none(
        Conversation.visitor_id == visitor_id,
        Conversation.status != "closed"
    )

    # A conversation row is NOT created on connect. An idle or proactively
    # auto-opened widget must never show up as a real conversation — the row is
    # born only when the visitor actually sends their first message (see
    # _ensure_conversation). Bot greetings / form prompts that auto-fire before
    # that message are buffered here and flushed into history the moment the
    # conversation starts, so nothing is lost from the transcript.
    pending_bot_texts: list[dict] = []

    async def _ensure_conversation():
        nonlocal conv
        if conv is not None:
            return conv
        geo = await asyncio.get_event_loop().run_in_executor(None, geo_lookup, client_ip)
        conv = Conversation.create(
            visitor_id=visitor_id,
            status="open",
            site_name=config.site.name,
            ip_address=client_ip,
            user_agent=user_agent,
            country=geo.get("country", ""),
            city=geo.get("city", ""),
            language=language,
        )
        for bt in pending_bot_texts:
            Message.create(
                conversation=conv, sender_type="bot", sender_id="bot",
                sender_name=bt["sender_name"], content=bt["content"],
            )
        pending_bot_texts.clear()
        # Tell the widget its real conversation id (history carried null until now).
        await ws.send_json({"type": "conversation_started", "conversation_id": conv.id})
        await manager.broadcast_to_agents({
            "type": "new_conversation",
            "conversation": _conv_dict(conv),
        })
        asyncio.create_task(fire_event("new_conversation", {
            "conversation": _conv_dict(conv),
        }))
        return conv

    # Send history (empty when the conversation hasn't started yet)
    history = list(conv.messages.order_by(Message.created_at)) if conv else []
    await ws.send_text(json.dumps({
        "type": "history",
        "messages": [_msg_dict(m) for m in history],
        "conversation_id": conv.id if conv else None,
        "config": {
            "color": config.chat.widget_color,
            "welcome_message": config.chat.welcome_message,
            "site_name": config.site.name,
            "agents_online": manager.agent_count() > 0,
        }
    }, ensure_ascii=False))

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "message")

            if msg_type == "message":
                content = str(data.get("content", "")).strip()
                if not content:
                    continue
                if len(content) > config.limits.max_message_length:
                    content = content[:config.limits.max_message_length]

                # First real visitor message — this is what creates the
                # conversation (and flushes any buffered bot greeting).
                await _ensure_conversation()

                visitor_name = data.get("visitor_name", conv.visitor_name) or "Visitor"
                visitor_email = data.get("visitor_email", conv.visitor_email) or ""
                page_url = data.get("page_url", conv.page_url) or ""

                if conv.visitor_name != visitor_name or conv.page_url != page_url:
                    Conversation.update(
                        visitor_name=visitor_name,
                        visitor_email=visitor_email,
                        page_url=page_url,
                        updated_at=datetime.utcnow()
                    ).where(Conversation.id == conv.id).execute()
                    conv.visitor_name = visitor_name

                msg = Message.create(
                    conversation=conv,
                    sender_type="visitor",
                    sender_id=visitor_id,
                    sender_name=visitor_name,
                    content=content,
                )

                payload = {
                    "type": "message",
                    "conversation_id": conv.id,
                    "message": _msg_dict(msg),
                }

                await manager.broadcast_to_watchers(conv.id, payload)
                await manager.broadcast_to_agents({**payload, "visitor_name": visitor_name})
                asyncio.create_task(fire_event("new_message", {
                    "conversation_id": conv.id,
                    "message": _msg_dict(msg),
                    "visitor_name": visitor_name,
                }))

                # Bot keyword rules take priority; AI auto-reply only fires
                # when no rule matched, so the two never double-reply.
                if conv.status == "open":
                    match = bot_matcher.find_best_match(content)
                    if match:
                        asyncio.create_task(_bot_rule_reply(conv, match))
                    elif config.ai.enabled and config.ai.auto_reply:
                        asyncio.create_task(_ai_reply(conv, msg))

            elif msg_type == "typing":
                if conv is None:
                    continue
                await manager.broadcast_to_watchers(conv.id, {
                    "type": "visitor_typing",
                    "conversation_id": conv.id,
                })

            elif msg_type == "read":
                if conv is None:
                    continue
                Message.update(is_read=True).where(
                    Message.conversation == conv,
                    Message.sender_type != "visitor"
                ).execute()

            elif msg_type == "page_view":
                url = str(data.get("url", ""))[:1024]
                title = str(data.get("title", ""))[:256]
                if url:
                    VisitorPageView.create(visitor_id=visitor_id, url=url, title=title)
                    if conv:
                        Conversation.update(page_url=url, updated_at=datetime.utcnow()).where(Conversation.id == conv.id).execute()
                        await manager.broadcast_to_agents({
                            "type": "visitor_page_view",
                            "visitor_id": visitor_id,
                            "conversation_id": conv.id if conv else None,
                            "url": url,
                            "title": title,
                        })

            elif msg_type == "set_department":
                if conv is None:
                    continue
                dept_id = int(data.get("department_id", 0) or 0)
                if dept_id and Department.get_or_none(Department.id == dept_id):
                    Conversation.update(
                        department_id=dept_id,
                        updated_at=datetime.utcnow()
                    ).where(Conversation.id == conv.id).execute()
                    dept = Department.get_by_id(dept_id)
                    await manager.broadcast_to_agents({
                        "type": "conv_department_changed",
                        "conversation_id": conv.id,
                        "department": {"id": dept.id, "name": dept.name, "color": dept.color, "icon": dept.icon},
                    })

            elif msg_type == "visitor_field":
                key = str(data.get("key", ""))[:64]
                value = str(data.get("value", ""))
                if key:
                    (VisitorField.insert(visitor_id=visitor_id, key=key, value=value)
                     .on_conflict(conflict_target=[VisitorField.visitor_id, VisitorField.key],
                                  update={VisitorField.value: value})
                     .execute())

            elif msg_type == "bot_text":
                # Relays bot/form-flow generated text (greeting, option reply,
                # form question, etc.) into real chat history so it survives
                # reconnects instead of living only in the widget's DOM.
                content = str(data.get("content", "")).strip()
                if not content:
                    continue
                content = content[:config.limits.max_message_length]
                sender_name = str(data.get("sender_name", "Bot")).strip()[:64] or "Bot"

                if conv is None:
                    # Greeting/form text fired before the visitor said anything —
                    # hold it; it'll be written once the conversation starts.
                    pending_bot_texts.append({"sender_name": sender_name, "content": content})
                    continue

                msg = Message.create(
                    conversation=conv,
                    sender_type="bot",
                    sender_id="bot",
                    sender_name=sender_name,
                    content=content,
                )
                Conversation.update(updated_at=datetime.utcnow()).where(Conversation.id == conv.id).execute()

                payload = {
                    "type": "message",
                    "conversation_id": conv.id,
                    "message": _msg_dict(msg),
                }
                await manager.broadcast_to_watchers(conv.id, payload)
                await manager.broadcast_to_agents({**payload, "visitor_name": conv.visitor_name})

    except WebSocketDisconnect:
        manager.disconnect_visitor(visitor_id)
        await manager.broadcast_to_agents({
            "type": "visitor_offline",
            "conversation_id": conv.id if conv else None,
            "visitor_id": visitor_id,
        })


@router.websocket("/ws/agent/{token}")
async def agent_ws(ws: WebSocket, token: str):
    """Agent WebSocket served under /ws/ so existing nginx upgrade rules apply."""
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
                conv_obj = Conversation.get_or_none(Conversation.id == int(data["conversation_id"]))
                if conv_obj:
                    updated = (Message.update(is_read=True)
                               .where(Message.conversation == conv_obj,
                                      Message.sender_type == "visitor",
                                      Message.is_read == False)
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


async def _bot_rule_reply(conv: Conversation, match: dict):
    await asyncio.sleep(0.6)
    fresh = Conversation.get_by_id(conv.id)
    if fresh.status == "assigned":
        return
    updates = {"updated_at": datetime.utcnow()}
    if match.get("department_id"):
        updates["department_id"] = match["department_id"]
    Conversation.update(**updates).where(Conversation.id == conv.id).execute()

    msg = Message.create(
        conversation=conv,
        sender_type="bot",
        sender_id="bot",
        sender_name=match.get("bot_name") or "Bot",
        content=match["reply"],
    )
    payload = {
        "type": "message",
        "conversation_id": conv.id,
        "message": _msg_dict(msg),
    }
    await manager.send_to_visitor(conv.visitor_id, payload)
    await manager.broadcast_to_watchers(conv.id, payload)
    await manager.broadcast_to_agents({**payload, "visitor_name": conv.visitor_name})


async def _ai_reply(conv: Conversation, trigger_msg: Message):
    await asyncio.sleep(1.2)
    # Re-check if agent took over while we waited
    fresh = Conversation.get_by_id(conv.id)
    if fresh.status == "assigned":
        return
    reply_text = await handle_ai_reply(conv, trigger_msg.content)
    if not reply_text:
        return
    msg = Message.create(
        conversation=conv,
        sender_type="bot",
        sender_name="Support Bot",
        content=reply_text,
    )
    payload = {
        "type": "message",
        "conversation_id": conv.id,
        "message": {
            "id": msg.id,
            "sender_type": "bot",
            "sender_name": "Support Bot",
            "content": reply_text,
            "file_url": "",
            "file_name": "",
            "created_at": msg.created_at.isoformat(),
        }
    }
    await manager.send_to_visitor(conv.visitor_id, payload)
    await manager.broadcast_to_watchers(conv.id, payload)
