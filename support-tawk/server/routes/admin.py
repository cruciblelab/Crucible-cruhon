from __future__ import annotations
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
from ..database import Agent, Conversation, Message, CannedResponse
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


# ── Config (public widget config) ─────────────────────────────────────────────

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
