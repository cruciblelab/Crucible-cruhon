from __future__ import annotations
import csv
import io
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from ..database import (
    Agent, Conversation, Message, CannedResponse,
    Tag, ConversationTag, BlacklistedIP, Rating, WorkSchedule, BotFlow
)
from ..auth import (
    hash_password, verify_password, create_token,
    get_current_agent, require_admin, verify_ws_token
)
from ..ws_manager import manager
from ..config import config

router = APIRouter(prefix="/api/admin")


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class AgentCreate(BaseModel):
    username: str
    password: str
    display_name: str = ""
    role: str = "agent"


class AgentUpdate(BaseModel):
    display_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class CannedCreate(BaseModel):
    title: str
    content: str
    shortcut: str = ""


class AssignRequest(BaseModel):
    conversation_id: int


class CloseRequest(BaseModel):
    conversation_id: int


class SendMessageRequest(BaseModel):
    conversation_id: int
    content: str


class TagCreate(BaseModel):
    name: str
    color: str = "#6366f1"


class ConvTagRequest(BaseModel):
    tag_id: int


class BlacklistCreate(BaseModel):
    ip: str
    reason: str = ""


class ScheduleUpdate(BaseModel):
    schedule_json: str
    timezone: str = "Europe/Istanbul"


class TransferRequest(BaseModel):
    conversation_id: int
    to_agent_id: int


class BotFlowCreate(BaseModel):
    name: str = "Ana Akış"
    greeting: str = "Merhaba! Size nasıl yardımcı olabilirim?"
    options_json: str = "[]"


class BotFlowUpdate(BaseModel):
    name: Optional[str] = None
    greeting: Optional[str] = None
    options_json: Optional[str] = None


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/login")
def login(req: LoginRequest):
    agent = Agent.get_or_none(Agent.username == req.username, Agent.is_active == True)
    if not agent or not verify_password(req.password, agent.password_hash):
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")
    token = create_token(agent.id, agent.role)
    return {
        "token": token,
        "agent": {
            "id": agent.id,
            "username": agent.username,
            "display_name": agent.display_name,
            "role": agent.role,
        }
    }


# ── Conversations ─────────────────────────────────────────────────────────────

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
    }


@router.get("/conversations")
def list_conversations(
    status: str = "open",
    agent: Agent = Depends(get_current_agent)
):
    query = Conversation.select().order_by(Conversation.updated_at.desc())
    if status != "all":
        query = query.where(Conversation.status == status)
    return [_conv_summary(c) for c in query]


@router.get("/conversations/mine")
def my_conversations(agent: Agent = Depends(get_current_agent)):
    convs = (Conversation.select()
             .where(Conversation.assigned_to == agent, Conversation.status != "closed")
             .order_by(Conversation.updated_at.desc()))
    return [_conv_summary(c) for c in convs]


@router.get("/conversations/export")
def export_all_conversations(
    days: int = 30,
    agent: Agent = Depends(get_current_agent)
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    convs = Conversation.select().where(Conversation.created_at >= cutoff).order_by(Conversation.created_at.desc())
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["conv_id", "visitor_name", "visitor_email", "status", "page_url", "created_at", "closed_at", "sender_type", "sender_name", "content", "created_at_msg"])
    for conv in convs:
        msgs = list(Message.select().where(Message.conversation == conv).order_by(Message.created_at))
        if not msgs:
            writer.writerow([conv.id, conv.visitor_name, conv.visitor_email, conv.status, conv.page_url, conv.created_at.isoformat(), conv.closed_at.isoformat() if conv.closed_at else "", "", "", "", ""])
        for msg in msgs:
            writer.writerow([conv.id, conv.visitor_name, conv.visitor_email, conv.status, conv.page_url, conv.created_at.isoformat(), conv.closed_at.isoformat() if conv.closed_at else "", msg.sender_type, msg.sender_name, msg.content, msg.created_at.isoformat()])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=conversations_{days}days.csv"}
    )


@router.get("/conversations/{conv_id}/export")
def export_conversation(conv_id: int, agent: Agent = Depends(get_current_agent)):
    conv = Conversation.get_or_none(Conversation.id == conv_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı")
    msgs = list(Message.select().where(Message.conversation == conv).order_by(Message.created_at))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "sender_type", "sender_name", "content", "file_url", "created_at"])
    for msg in msgs:
        writer.writerow([msg.id, msg.sender_type, msg.sender_name, msg.content, msg.file_url, msg.created_at.isoformat()])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=conv_{conv_id}.csv"}
    )


@router.get("/conversations/{conv_id}")
def get_conversation(conv_id: int, agent: Agent = Depends(get_current_agent)):
    conv = Conversation.get_or_none(Conversation.id == conv_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı")
    return _conv_full(conv)


@router.post("/conversations/assign")
async def assign_conversation(req: AssignRequest, agent: Agent = Depends(get_current_agent)):
    conv = Conversation.get_or_none(Conversation.id == req.conversation_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı")
    Conversation.update(
        status="assigned",
        assigned_to=agent,
        updated_at=datetime.utcnow()
    ).where(Conversation.id == conv.id).execute()

    sys_msg = Message.create(
        conversation=conv,
        sender_type="system",
        sender_name="Sistem",
        content=f"{agent.display_name or agent.username} konuşmayı devraldı.",
    )

    notify = {
        "type": "conversation_assigned",
        "conversation_id": conv.id,
        "agent": {"id": agent.id, "username": agent.username, "display_name": agent.display_name},
        "message": _msg_dict(sys_msg),
    }
    await manager.send_to_visitor(conv.visitor_id, {"type": "message", "message": _msg_dict(sys_msg)})
    await manager.broadcast_to_agents(notify)
    return {"ok": True}


@router.post("/conversations/close")
async def close_conversation(req: CloseRequest, agent: Agent = Depends(get_current_agent)):
    conv = Conversation.get_or_none(Conversation.id == req.conversation_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı")
    Conversation.update(
        status="closed",
        closed_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ).where(Conversation.id == conv.id).execute()

    await manager.send_to_visitor(conv.visitor_id, {
        "type": "conversation_closed",
        "message": "Konuşma kapatıldı. Teşekkürler."
    })
    await manager.broadcast_to_agents({
        "type": "conversation_closed",
        "conversation_id": conv.id,
    })
    return {"ok": True}


@router.post("/conversations/send")
async def send_message(req: SendMessageRequest, agent: Agent = Depends(get_current_agent)):
    conv = Conversation.get_or_none(Conversation.id == req.conversation_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı")
    content = req.content.strip()
    if not content:
        raise HTTPException(400, "Mesaj boş olamaz")

    msg = Message.create(
        conversation=conv,
        sender_type="agent",
        sender_id=str(agent.id),
        sender_name=agent.display_name or agent.username,
        content=content,
    )
    Conversation.update(updated_at=datetime.utcnow()).where(Conversation.id == conv.id).execute()

    payload = {
        "type": "message",
        "conversation_id": conv.id,
        "message": _msg_dict(msg),
    }
    await manager.send_to_visitor(conv.visitor_id, payload)
    await manager.broadcast_to_watchers(conv.id, payload)
    return _msg_dict(msg)


@router.post("/conversations/transfer")
async def transfer_conversation(req: TransferRequest, agent: Agent = Depends(get_current_agent)):
    conv = Conversation.get_or_none(Conversation.id == req.conversation_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı")
    target = Agent.get_or_none(Agent.id == req.to_agent_id)
    if not target:
        raise HTTPException(404, "Hedef temsilci bulunamadı")
    Conversation.update(
        assigned_to=target,
        status="assigned",
        updated_at=datetime.utcnow()
    ).where(Conversation.id == conv.id).execute()
    sys_msg = Message.create(
        conversation=conv,
        sender_type="system",
        sender_name="Sistem",
        content=f"Konuşma {target.display_name or target.username} temsilcisine aktarıldı.",
    )
    await manager.send_to_visitor(conv.visitor_id, {"type": "message", "message": _msg_dict(sys_msg)})
    await manager.broadcast_to_agents({
        "type": "conversation_assigned",
        "conversation_id": conv.id,
        "agent": {"id": target.id, "username": target.username, "display_name": target.display_name},
        "message": _msg_dict(sys_msg),
    })
    return {"ok": True}


@router.post("/conversations/{conv_id}/tags")
def add_conv_tag(conv_id: int, req: ConvTagRequest, agent: Agent = Depends(get_current_agent)):
    conv = Conversation.get_or_none(Conversation.id == conv_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı")
    tag = Tag.get_or_none(Tag.id == req.tag_id)
    if not tag:
        raise HTTPException(404, "Etiket bulunamadı")
    ConversationTag.get_or_create(conversation=conv, tag=tag)
    return {"ok": True}


@router.delete("/conversations/{conv_id}/tags/{tag_id}")
def remove_conv_tag(conv_id: int, tag_id: int, agent: Agent = Depends(get_current_agent)):
    ConversationTag.delete().where(
        ConversationTag.conversation_id == conv_id,
        ConversationTag.tag_id == tag_id
    ).execute()
    return {"ok": True}


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
            "is_active": a.is_active,
            "is_online": a.id in manager.online_agents(),
            "created_at": a.created_at.isoformat(),
        }
        for a in agents
    ]


@router.post("/agents")
def create_agent(req: AgentCreate, admin: Agent = Depends(require_admin)):
    if Agent.get_or_none(Agent.username == req.username):
        raise HTTPException(400, "Bu kullanıcı adı zaten kullanılıyor")
    a = Agent.create(
        username=req.username,
        password_hash=hash_password(req.password),
        display_name=req.display_name or req.username,
        role=req.role,
    )
    return {"id": a.id, "username": a.username, "role": a.role}


@router.patch("/agents/{agent_id}")
def update_agent(agent_id: int, req: AgentUpdate, admin: Agent = Depends(require_admin)):
    a = Agent.get_or_none(Agent.id == agent_id)
    if not a:
        raise HTTPException(404, "Kullanıcı bulunamadı")
    updates = {}
    if req.display_name is not None:
        updates["display_name"] = req.display_name
    if req.role is not None:
        updates["role"] = req.role
    if req.is_active is not None:
        updates["is_active"] = req.is_active
    if req.password is not None:
        updates["password_hash"] = hash_password(req.password)
    if updates:
        Agent.update(**updates).where(Agent.id == agent_id).execute()
    return {"ok": True}


@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: int, admin: Agent = Depends(require_admin)):
    Agent.delete().where(Agent.id == agent_id).execute()
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
def create_tag(req: TagCreate, agent: Agent = Depends(get_current_agent)):
    if Tag.get_or_none(Tag.name == req.name):
        raise HTTPException(400, "Bu isimde etiket zaten var")
    t = Tag.create(name=req.name, color=req.color)
    return {"id": t.id, "name": t.name, "color": t.color}


@router.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, agent: Agent = Depends(get_current_agent)):
    Tag.delete().where(Tag.id == tag_id).execute()
    return {"ok": True}


# ── IP Blacklist ──────────────────────────────────────────────────────────────

@router.get("/blacklist")
def list_blacklist(agent: Agent = Depends(get_current_agent)):
    return [
        {
            "id": b.id,
            "ip": b.ip,
            "reason": b.reason,
            "blocked_by": b.blocked_by_id,
            "created_at": b.created_at.isoformat(),
        }
        for b in BlacklistedIP.select().order_by(BlacklistedIP.created_at.desc())
    ]


@router.post("/blacklist")
def add_blacklist(req: BlacklistCreate, agent: Agent = Depends(get_current_agent)):
    if BlacklistedIP.get_or_none(BlacklistedIP.ip == req.ip):
        raise HTTPException(400, "Bu IP zaten yasaklı")
    b = BlacklistedIP.create(ip=req.ip, reason=req.reason, blocked_by=agent)
    return {"id": b.id, "ip": b.ip}


@router.delete("/blacklist/{bl_id}")
def remove_blacklist(bl_id: int, agent: Agent = Depends(get_current_agent)):
    BlacklistedIP.delete().where(BlacklistedIP.id == bl_id).execute()
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
def update_schedule(agent_id: int, req: ScheduleUpdate, agent: Agent = Depends(get_current_agent)):
    target = Agent.get_or_none(Agent.id == agent_id)
    if not target:
        raise HTTPException(404, "Temsilci bulunamadı")
    sched, _ = WorkSchedule.get_or_create(agent=target)
    WorkSchedule.update(
        schedule_json=req.schedule_json,
        timezone=req.timezone
    ).where(WorkSchedule.id == sched.id).execute()
    return {"ok": True}


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(agent: Agent = Depends(get_current_agent)):
    return {
        "open": Conversation.select().where(Conversation.status == "open").count(),
        "assigned": Conversation.select().where(Conversation.status == "assigned").count(),
        "closed_today": Conversation.select().where(
            Conversation.status == "closed",
            Conversation.closed_at >= datetime.utcnow().date()
        ).count(),
        "agents_online": manager.agent_count(),
        "visitors_online": manager.visitor_count(),
    }


@router.get("/stats/detailed")
def get_detailed_stats(agent: Agent = Depends(get_current_agent)):
    cutoff30 = datetime.utcnow() - timedelta(days=30)

    # daily conversations last 30 days
    daily: dict[str, int] = {}
    for i in range(30):
        d = (datetime.utcnow() - timedelta(days=i)).date()
        daily[str(d)] = 0
    for conv in Conversation.select().where(Conversation.created_at >= cutoff30):
        day_str = conv.created_at.date().isoformat()
        if day_str in daily:
            daily[day_str] = daily[day_str] + 1
    daily_list = [{"date": k, "count": v} for k, v in sorted(daily.items())]

    # avg response time (minutes)
    response_times: list[float] = []
    for conv in Conversation.select().where(Conversation.created_at >= cutoff30):
        first_visitor = (Message.select()
                         .where(Message.conversation == conv, Message.sender_type == "visitor")
                         .order_by(Message.created_at).first())
        first_agent = (Message.select()
                       .where(Message.conversation == conv, Message.sender_type.in_(["agent", "bot"]))
                       .order_by(Message.created_at).first())
        if first_visitor and first_agent and first_agent.created_at > first_visitor.created_at:
            diff = (first_agent.created_at - first_visitor.created_at).total_seconds() / 60.0
            response_times.append(diff)
    avg_response = round(sum(response_times) / len(response_times), 1) if response_times else 0.0

    # avg rating
    ratings = list(Rating.select().where(Rating.created_at >= cutoff30))
    avg_rating = round(sum(r.score for r in ratings) / len(ratings), 1) if ratings else 0.0

    # total conversations
    total = Conversation.select().count()

    # top agents
    agent_counts: dict[str, int] = {}
    for conv in Conversation.select().where(Conversation.created_at >= cutoff30, Conversation.assigned_to.is_null(False)):
        if conv.assigned_to_id:
            a = Agent.get_or_none(Agent.id == conv.assigned_to_id)
            if a:
                name = a.display_name or a.username
                agent_counts[name] = agent_counts.get(name, 0) + 1
    top_agents = sorted([{"agent_name": k, "count": v} for k, v in agent_counts.items()], key=lambda x: -x["count"])[:5]

    # hourly distribution
    hourly: dict[int, int] = {h: 0 for h in range(24)}
    for conv in Conversation.select().where(Conversation.created_at >= cutoff30):
        hourly[conv.created_at.hour] = hourly[conv.created_at.hour] + 1
    hourly_list = [{"hour": h, "count": hourly[h]} for h in range(24)]

    return {
        "daily_conversations": daily_list,
        "avg_response_minutes": avg_response,
        "avg_rating": avg_rating,
        "total_conversations": total,
        "top_agents": top_agents,
        "hourly_distribution": hourly_list,
    }


# ── Bot Flow ──────────────────────────────────────────────────────────────────

@router.get("/botflow")
def list_botflows(agent: Agent = Depends(get_current_agent)):
    return [
        {
            "id": b.id,
            "name": b.name,
            "greeting": b.greeting,
            "options_json": b.options_json,
            "is_active": b.is_active,
            "created_at": b.created_at.isoformat(),
        }
        for b in BotFlow.select().order_by(BotFlow.created_at.desc())
    ]


@router.post("/botflow")
def create_botflow(req: BotFlowCreate, agent: Agent = Depends(get_current_agent)):
    b = BotFlow.create(name=req.name, greeting=req.greeting, options_json=req.options_json)
    return {"id": b.id, "name": b.name}


@router.put("/botflow/{flow_id}")
def update_botflow(flow_id: int, req: BotFlowUpdate, agent: Agent = Depends(get_current_agent)):
    b = BotFlow.get_or_none(BotFlow.id == flow_id)
    if not b:
        raise HTTPException(404, "Bot akışı bulunamadı")
    updates = {}
    if req.name is not None:
        updates["name"] = req.name
    if req.greeting is not None:
        updates["greeting"] = req.greeting
    if req.options_json is not None:
        updates["options_json"] = req.options_json
    if updates:
        BotFlow.update(**updates).where(BotFlow.id == flow_id).execute()
    return {"ok": True}


@router.delete("/botflow/{flow_id}")
def delete_botflow(flow_id: int, agent: Agent = Depends(get_current_agent)):
    BotFlow.delete().where(BotFlow.id == flow_id).execute()
    return {"ok": True}


@router.post("/botflow/{flow_id}/activate")
def activate_botflow(flow_id: int, agent: Agent = Depends(get_current_agent)):
    b = BotFlow.get_or_none(BotFlow.id == flow_id)
    if not b:
        raise HTTPException(404, "Bot akışı bulunamadı")
    BotFlow.update(is_active=False).execute()
    BotFlow.update(is_active=True).where(BotFlow.id == flow_id).execute()
    return {"ok": True}
