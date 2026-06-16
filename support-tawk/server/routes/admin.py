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
from ..database import (
    Department, Agent, Conversation, Message, CannedResponse,
    Tag, ConversationTag, BlacklistedIP, Rating, WorkSchedule, BotFlow, Setting,
    Note, WebhookConfig, VisitorPageView, VisitorField, AuditLog, OfflineMessage,
    Form, FormField, FormSubmission,
)
from ..webhook_sender import fire_event
from ..auth import (
    hash_password, verify_password, create_token,
    get_current_agent, require_admin, require_permission, verify_ws_token,
    agent_permissions, validate_password_strength, PERMISSIONS,
)
from ..ws_manager import manager
from ..config import config
from .. import seclog

router = APIRouter(prefix="/api/admin")


def _audit(agent_name: str, action: str, target_type: str = "", target_id: int = None, details: str = ""):
    AuditLog.create(agent_name=agent_name, action=action, target_type=target_type, target_id=target_id, details=details)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class AgentCreate(BaseModel):
    username: str
    password: str
    display_name: str = ""
    role: str = "agent"
    permissions: Optional[List[str]] = None


class AgentUpdate(BaseModel):
    display_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    department_id: Optional[int] = None
    permissions: Optional[List[str]] = None


class DepartmentCreate(BaseModel):
    name: str
    description: str = ""
    color: str = "#6366f1"
    icon: str = "💼"


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class ConvDeptRequest(BaseModel):
    department_id: Optional[int] = None


class CannedCreate(BaseModel):
    title: str
    content: str
    shortcut: str = ""


class AssignRequest(BaseModel):
    conversation_id: int


class CloseRequest(BaseModel):
    conversation_id: int
    send_rating: bool = True


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
    kind: str = "ip"  # ip | visitor


class PriorityUpdate(BaseModel):
    priority: str  # low | normal | high


class BulkActionRequest(BaseModel):
    conversation_ids: List[int]
    action: str  # close | assign | reopen
    tag_id: Optional[int] = None


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


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    password: Optional[str] = None
    avatar_color: Optional[str] = None


class AppSettingsUpdate(BaseModel):
    site_name: Optional[str] = None
    widget_color: Optional[str] = None
    welcome_message: Optional[str] = None
    offline_message: Optional[str] = None
    proactive_delay_seconds: Optional[int] = None
    notification_sound: Optional[bool] = None
    widget_width: Optional[int] = None
    proactive_bubbles: Optional[str] = None  # JSON dizisi: ["mesaj1", "mesaj2"]
    # Görünüm & dil
    widget_position: Optional[str] = None  # right | left
    language: Optional[str] = None          # en | tr
    widget_icon: Optional[str] = None      # buton ikonu (emoji)
    widget_radius: Optional[int] = None    # köşe yuvarlaklığı (px)
    widget_texts: Optional[str] = None     # JSON: {"key": "metin", ...} dil metni geçersiz kılma
    bubble_dismiss_days: Optional[int] = None  # 0=oturum, N=N gün


class NoteCreate(BaseModel):
    content: str

class WebhookCreate(BaseModel):
    name: str = "Webhook"
    type: str
    url: str
    telegram_chat_id: str = ""
    events_json: str = '["new_conversation","new_message","offline_message"]'
    is_enabled: bool = True

class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    events_json: Optional[str] = None
    is_enabled: Optional[bool] = None

class VisitorFieldCreate(BaseModel):
    key: str
    value: str

class FormCreate(BaseModel):
    name: str
    description: str = ""
    welcome_text: str = "Lütfen aşağıdaki formu doldurun."
    submit_text: str = "Gönder"
    department_id: Optional[int] = None

class FormUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    welcome_text: Optional[str] = None
    submit_text: Optional[str] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None

class FormFieldCreate(BaseModel):
    label: str
    field_type: str = "text"
    required: bool = True
    placeholder: str = ""
    options_json: str = "[]"
    order: int = 0

class FormFieldUpdate(BaseModel):
    label: Optional[str] = None
    field_type: Optional[str] = None
    required: Optional[bool] = None
    placeholder: Optional[str] = None
    options_json: Optional[str] = None
    order: Optional[int] = None

class FieldOrderRequest(BaseModel):
    field_ids: List[int]


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/login")
def login(req: LoginRequest, request: Request):
    ip = seclog.client_ip(request)
    agent = Agent.get_or_none(Agent.username == req.username, Agent.is_active == True)
    if not agent or not verify_password(req.password, agent.password_hash):
        seclog.login_failed(ip, req.username)
        raise HTTPException(status_code=401, detail="Invalid username or password")
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


@router.get("/conversations")
def list_conversations(
    status: str = "open",
    unread_only: bool = False,
    priority: str = "",
    department_id: int = 0,
    agent: Agent = Depends(get_current_agent)
):
    query = Conversation.select().order_by(Conversation.updated_at.desc())
    if status != "all":
        query = query.where(Conversation.status == status)
    if priority in ("low", "normal", "high"):
        query = query.where(Conversation.priority == priority)
    if department_id:
        query = query.where(Conversation.department_id == department_id)
    summaries = [_conv_summary(c) for c in query]
    if unread_only:
        summaries = [s for s in summaries if s["unread_count"] > 0]
    return summaries


@router.get("/conversations/dept")
def dept_conversations(agent: Agent = Depends(get_current_agent)):
    """Temsilcinin kendi departmanına atanmış açık konuşmalar."""
    dept_id = getattr(agent, "department_id", None)
    if not dept_id:
        return []
    query = (Conversation.select()
             .where(Conversation.department_id == dept_id, Conversation.status != "closed")
             .order_by(Conversation.updated_at.desc()))
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
    agent: Agent = Depends(require_permission("export_data"))
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
    _audit(agent.display_name or agent.username, "assign", "conversation", conv.id, "Atandı")

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
    _audit(agent.display_name or agent.username, "close", "conversation", conv.id)

    await manager.send_to_visitor(conv.visitor_id, {
        "type": "conversation_closed",
        "message": "Konuşma kapatıldı. Teşekkürler.",
        "request_rating": req.send_rating,
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
    await manager.broadcast_to_watchers_except(conv.id, payload, agent.id)
    return _msg_dict(msg)


@router.post("/conversations/reopen")
async def reopen_conversation(req: CloseRequest, agent: Agent = Depends(get_current_agent)):
    conv = Conversation.get_or_none(Conversation.id == req.conversation_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı")
    Conversation.update(
        status="open",
        closed_at=None,
        updated_at=datetime.utcnow()
    ).where(Conversation.id == conv.id).execute()
    _audit(agent.display_name or agent.username, "reopen", "conversation", conv.id)
    await manager.broadcast_to_agents({
        "type": "conversation_reopened",
        "conversation_id": conv.id,
    })
    return {"ok": True}


@router.patch("/conversations/{conv_id}/priority")
def set_priority(conv_id: int, req: PriorityUpdate, agent: Agent = Depends(get_current_agent)):
    if req.priority not in ("low", "normal", "high"):
        raise HTTPException(400, "Geçersiz öncelik")
    conv = Conversation.get_or_none(Conversation.id == conv_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı")
    Conversation.update(priority=req.priority, updated_at=datetime.utcnow()).where(Conversation.id == conv_id).execute()
    return {"ok": True}


@router.post("/conversations/bulk")
async def bulk_action(req: BulkActionRequest, agent: Agent = Depends(get_current_agent)):
    if not req.conversation_ids:
        raise HTTPException(400, "Konuşma seçilmedi")
    if req.action not in ("close", "assign", "reopen", "tag"):
        raise HTTPException(400, "Geçersiz işlem")

    results = {"ok": 0, "failed": 0}
    now = datetime.utcnow()

    for conv_id in req.conversation_ids:
        conv = Conversation.get_or_none(Conversation.id == conv_id)
        if not conv:
            results["failed"] += 1
            continue
        try:
            if req.action == "close":
                Conversation.update(status="closed", closed_at=now, updated_at=now).where(Conversation.id == conv_id).execute()
                await manager.send_to_visitor(conv.visitor_id, {"type": "conversation_closed"})
            elif req.action == "assign":
                Conversation.update(status="assigned", assigned_to=agent, updated_at=now).where(Conversation.id == conv_id).execute()
            elif req.action == "reopen":
                Conversation.update(status="open", closed_at=None, updated_at=now).where(Conversation.id == conv_id).execute()
            elif req.action == "tag" and req.tag_id:
                from ..database import Tag, ConversationTag
                tag = Tag.get_or_none(Tag.id == req.tag_id)
                if tag:
                    ConversationTag.get_or_create(conversation=conv, tag=tag)
            results["ok"] += 1
        except Exception:
            results["failed"] += 1

    _audit(agent.display_name or agent.username, f"bulk_{req.action}", "conversations", None,
           f"{results['ok']} konuşma")
    await manager.broadcast_to_agents({"type": "bulk_action_done", "action": req.action})
    return results


@router.get("/conversations/export-xlsx")
def export_xlsx(days: int = 30, agent: Agent = Depends(require_permission("export_data"))):
    if not _HAS_OPENPYXL:
        raise HTTPException(501, "openpyxl kurulu değil — CSV kullanın")
    cutoff = datetime.utcnow() - timedelta(days=days)
    convs = Conversation.select().where(Conversation.created_at >= cutoff).order_by(Conversation.created_at.desc())
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Konuşmalar"
    headers = ["ID", "Ziyaretçi", "E-posta", "Durum", "Öncelik", "IP", "Ülke", "Şehir", "Dil", "Sayfa", "Oluşturma", "Kapanma", "Gönderen", "Mesaj İçeriği", "Mesaj Zamanı"]
    ws.append(headers)
    for conv in convs:
        msgs = list(Message.select().where(Message.conversation == conv).order_by(Message.created_at))
        if not msgs:
            ws.append([
                conv.id, conv.visitor_name, conv.visitor_email, conv.status,
                getattr(conv, "priority", "normal"),
                getattr(conv, "ip_address", ""), getattr(conv, "country", ""),
                getattr(conv, "city", ""), getattr(conv, "language", ""),
                conv.page_url, conv.created_at.isoformat(),
                conv.closed_at.isoformat() if conv.closed_at else "", "", "", ""
            ])
        for msg in msgs:
            ws.append([
                conv.id, conv.visitor_name, conv.visitor_email, conv.status,
                getattr(conv, "priority", "normal"),
                getattr(conv, "ip_address", ""), getattr(conv, "country", ""),
                getattr(conv, "city", ""), getattr(conv, "language", ""),
                conv.page_url, conv.created_at.isoformat(),
                conv.closed_at.isoformat() if conv.closed_at else "",
                msg.sender_name, msg.content, msg.created_at.isoformat()
            ])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=conversations_{days}days.xlsx"}
    )


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
    _audit(agent.display_name or agent.username, "transfer", "conversation", conv.id, f"→ {target.display_name or target.username}")
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


@router.patch("/conversations/{conv_id}/department")
async def set_conv_department(conv_id: int, req: ConvDeptRequest, agent: Agent = Depends(get_current_agent)):
    conv = Conversation.get_or_none(Conversation.id == conv_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı")
    dept = None
    if req.department_id:
        dept = Department.get_or_none(Department.id == req.department_id)
        if not dept:
            raise HTTPException(404, "Departman bulunamadı")
    Conversation.update(
        department_id=req.department_id,
        updated_at=datetime.utcnow()
    ).where(Conversation.id == conv_id).execute()
    _audit(agent.display_name or agent.username, "set_department", "conversation", conv_id,
           dept.name if dept else "Yok")
    dept_info = {"id": dept.id, "name": dept.name, "color": dept.color, "icon": dept.icon} if dept else None
    await manager.broadcast_to_agents({
        "type": "conv_department_changed",
        "conversation_id": conv_id,
        "department": dept_info,
    })
    return {"ok": True, "department": dept_info}


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
    from ..settings_cache import invalidate as _invalidate_settings
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
def add_blacklist(req: BlacklistCreate, agent: Agent = Depends(require_permission("manage_blacklist"))):
    kind = req.kind if req.kind in ("ip", "visitor") else "ip"
    if BlacklistedIP.get_or_none(BlacklistedIP.ip == req.ip):
        raise HTTPException(400, "Bu değer zaten yasaklı")
    b = BlacklistedIP.create(ip=req.ip, reason=req.reason, blocked_by=agent, kind=kind)
    _audit(agent.display_name or agent.username, "blacklist_add", kind, b.id, req.ip)
    return {"id": b.id, "ip": b.ip, "kind": kind}


@router.delete("/blacklist/{bl_id}")
def remove_blacklist(bl_id: int, agent: Agent = Depends(require_permission("manage_blacklist"))):
    _audit(agent.display_name or agent.username, "blacklist_remove", "ip", bl_id)
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
def get_detailed_stats(days: int = 30, agent: Agent = Depends(get_current_agent)):
    days = max(1, min(365, days))
    cutoff = datetime.utcnow() - timedelta(days=days)
    period_convs = list(Conversation.select().where(Conversation.created_at >= cutoff))

    # daily conversations
    daily: dict[str, int] = {}
    for i in range(days):
        d = (datetime.utcnow() - timedelta(days=i)).date()
        daily[str(d)] = 0
    for conv in period_convs:
        day_str = conv.created_at.date().isoformat()
        if day_str in daily:
            daily[day_str] = daily[day_str] + 1
    daily_list = [{"date": k, "count": v} for k, v in sorted(daily.items())]
    busiest_day = max(daily_list, key=lambda x: x["count"]) if daily_list else {"date": "", "count": 0}

    # avg + median response time (minutes)
    response_times: list[float] = []
    for conv in period_convs:
        first_visitor = (Message.select()
                         .where(Message.conversation == conv, Message.sender_type == "visitor")
                         .order_by(Message.created_at).first())
        first_agent = (Message.select()
                       .where(Message.conversation == conv, Message.sender_type == "agent")
                       .order_by(Message.created_at).first())
        if first_visitor and first_agent and first_agent.created_at > first_visitor.created_at:
            diff = (first_agent.created_at - first_visitor.created_at).total_seconds() / 60.0
            response_times.append(diff)
    avg_response = round(sum(response_times) / len(response_times), 1) if response_times else 0.0
    if response_times:
        srt = sorted(response_times)
        mid = len(srt) // 2
        median_response = round((srt[mid] if len(srt) % 2 else (srt[mid - 1] + srt[mid]) / 2), 1)
    else:
        median_response = 0.0

    # ratings: avg + distribution (1-5)
    ratings = list(Rating.select().where(Rating.created_at >= cutoff))
    avg_rating = round(sum(r.score for r in ratings) / len(ratings), 1) if ratings else 0.0
    rating_dist = {s: 0 for s in range(1, 6)}
    for r in ratings:
        if r.score in rating_dist:
            rating_dist[r.score] += 1
    rating_distribution = [{"score": s, "count": rating_dist[s]} for s in range(1, 6)]

    # total + status breakdown + resolution rate
    total = Conversation.select().count()
    period_total = len(period_convs)
    closed_count = sum(1 for c in period_convs if c.status == "closed")
    open_count = sum(1 for c in period_convs if c.status == "open")
    assigned_count = sum(1 for c in period_convs if c.status == "assigned")
    resolution_rate = round((closed_count / period_total) * 100, 1) if period_total else 0.0

    # total messages in period
    conv_ids = [c.id for c in period_convs]
    total_messages = (Message.select().where(Message.conversation.in_(conv_ids)).count()
                      if conv_ids else 0)

    # top agents (by closed convs assigned to them)
    agent_counts: dict[str, int] = {}
    for conv in period_convs:
        if conv.assigned_to_id:
            a = Agent.get_or_none(Agent.id == conv.assigned_to_id)
            if a:
                name = a.display_name or a.username
                agent_counts[name] = agent_counts.get(name, 0) + 1
    top_agents = sorted([{"agent_name": k, "count": v} for k, v in agent_counts.items()], key=lambda x: -x["count"])[:8]

    # department breakdown
    dept_counts: dict[str, dict] = {}
    for conv in period_convs:
        dep_id = getattr(conv, "department_id", None)
        if dep_id:
            d = Department.get_or_none(Department.id == dep_id)
            if d:
                key = d.name
                if key not in dept_counts:
                    dept_counts[key] = {"name": d.name, "icon": d.icon, "color": d.color, "count": 0}
                dept_counts[key]["count"] += 1
    department_breakdown = sorted(dept_counts.values(), key=lambda x: -x["count"])

    # hourly distribution
    hourly: dict[int, int] = {h: 0 for h in range(24)}
    for conv in period_convs:
        hourly[conv.created_at.hour] = hourly[conv.created_at.hour] + 1
    hourly_list = [{"hour": h, "count": hourly[h]} for h in range(24)]

    return {
        "days": days,
        "daily_conversations": daily_list,
        "avg_response_minutes": avg_response,
        "median_response_minutes": median_response,
        "avg_rating": avg_rating,
        "rating_distribution": rating_distribution,
        "rating_count": len(ratings),
        "total_conversations": total,
        "period_conversations": period_total,
        "status_breakdown": {"open": open_count, "assigned": assigned_count, "closed": closed_count},
        "resolution_rate": resolution_rate,
        "total_messages": total_messages,
        "busiest_day": busiest_day,
        "top_agents": top_agents,
        "department_breakdown": department_breakdown,
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
def create_botflow(req: BotFlowCreate, agent: Agent = Depends(require_permission("manage_botflow"))):
    b = BotFlow.create(name=req.name, greeting=req.greeting, options_json=req.options_json)
    return {"id": b.id, "name": b.name}


@router.put("/botflow/{flow_id}")
def update_botflow(flow_id: int, req: BotFlowUpdate, agent: Agent = Depends(require_permission("manage_botflow"))):
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
def delete_botflow(flow_id: int, agent: Agent = Depends(require_permission("manage_botflow"))):
    BotFlow.delete().where(BotFlow.id == flow_id).execute()
    return {"ok": True}


@router.post("/botflow/{flow_id}/activate")
def activate_botflow(flow_id: int, agent: Agent = Depends(require_permission("manage_botflow"))):
    b = BotFlow.get_or_none(BotFlow.id == flow_id)
    if not b:
        raise HTTPException(404, "Bot akışı bulunamadı")
    BotFlow.update(is_active=False).execute()
    BotFlow.update(is_active=True).where(BotFlow.id == flow_id).execute()
    return {"ok": True}


# ── Notes ─────────────────────────────────────────────────────────────────────

@router.get("/conversations/{conv_id}/notes")
def get_notes(conv_id: int, agent: Agent = Depends(get_current_agent)):
    conv = Conversation.get_or_none(Conversation.id == conv_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı")
    return [
        {"id": n.id, "content": n.content, "agent_name": n.agent_name, "created_at": n.created_at.isoformat()}
        for n in Note.select().where(Note.conversation == conv).order_by(Note.created_at)
    ]

@router.post("/conversations/{conv_id}/notes")
def create_note(conv_id: int, req: NoteCreate, agent: Agent = Depends(get_current_agent)):
    conv = Conversation.get_or_none(Conversation.id == conv_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı")
    n = Note.create(
        conversation=conv,
        agent=agent,
        agent_name=agent.display_name or agent.username,
        content=req.content.strip(),
    )
    return {"id": n.id, "content": n.content, "agent_name": n.agent_name, "created_at": n.created_at.isoformat()}

@router.delete("/conversations/{conv_id}/notes/{note_id}")
def delete_note(conv_id: int, note_id: int, agent: Agent = Depends(get_current_agent)):
    Note.delete().where(Note.id == note_id, Note.conversation_id == conv_id).execute()
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


# ── Visitor history ───────────────────────────────────────────────────────────

@router.get("/visitors/{visitor_id}/history")
def visitor_history(visitor_id: str, agent: Agent = Depends(get_current_agent)):
    convs = (Conversation.select()
             .where(Conversation.visitor_id == visitor_id)
             .order_by(Conversation.created_at.desc())
             .limit(20))
    return [_conv_summary(c) for c in convs]

@router.get("/visitors/{visitor_id}/pages")
def visitor_pages(visitor_id: str, agent: Agent = Depends(get_current_agent)):
    pages = (VisitorPageView.select()
             .where(VisitorPageView.visitor_id == visitor_id)
             .order_by(VisitorPageView.created_at.desc())
             .limit(50))
    return [{"url": p.url, "title": p.title, "created_at": p.created_at.isoformat()} for p in pages]

@router.get("/visitors/{visitor_id}/fields")
def get_visitor_fields(visitor_id: str, agent: Agent = Depends(get_current_agent)):
    return [{"key": f.key, "value": f.value} for f in VisitorField.select().where(VisitorField.visitor_id == visitor_id)]

@router.post("/visitors/{visitor_id}/fields")
def set_visitor_field(visitor_id: str, req: VisitorFieldCreate, agent: Agent = Depends(get_current_agent)):
    (VisitorField.insert(visitor_id=visitor_id, key=req.key, value=req.value)
     .on_conflict(conflict_target=[VisitorField.visitor_id, VisitorField.key],
                  update={VisitorField.value: req.value})
     .execute())
    return {"ok": True}

@router.delete("/visitors/{visitor_id}/fields/{key}")
def delete_visitor_field(visitor_id: str, key: str, agent: Agent = Depends(get_current_agent)):
    VisitorField.delete().where(VisitorField.visitor_id == visitor_id, VisitorField.key == key).execute()
    return {"ok": True}


@router.delete("/visitors/{visitor_id}/data")
def delete_visitor_data(visitor_id: str, admin: Agent = Depends(require_permission("delete_data"))):
    conv_ids = [c.id for c in Conversation.select(Conversation.id).where(Conversation.visitor_id == visitor_id)]
    if conv_ids:
        Message.delete().where(Message.conversation_id.in_(conv_ids)).execute()
        Note.delete().where(Note.conversation_id.in_(conv_ids)).execute()
        Rating.delete().where(Rating.conversation_id.in_(conv_ids)).execute()
        ConversationTag.delete().where(ConversationTag.conversation_id.in_(conv_ids)).execute()
        FormSubmission.delete().where(FormSubmission.conversation_id.in_(conv_ids)).execute()
        Conversation.delete().where(Conversation.id.in_(conv_ids)).execute()
    FormSubmission.delete().where(FormSubmission.visitor_id == visitor_id).execute()
    VisitorField.delete().where(VisitorField.visitor_id == visitor_id).execute()
    VisitorPageView.delete().where(VisitorPageView.visitor_id == visitor_id).execute()
    OfflineMessage.delete().where(OfflineMessage.visitor_id == visitor_id).execute()
    _audit(admin.display_name or admin.username, "delete_visitor_data", "visitor", None, visitor_id)
    return {"ok": True}


# ── Live visitors ─────────────────────────────────────────────────────────────

@router.get("/live-visitors")
def live_visitors(agent: Agent = Depends(get_current_agent)):
    from ..ws_manager import manager
    visitor_ids = list(manager.live_visitors().keys())
    result = []
    for vid in visitor_ids:
        conv = (Conversation.select()
                .where(Conversation.visitor_id == vid, Conversation.status != "closed")
                .order_by(Conversation.updated_at.desc())
                .first())
        last_page = (VisitorPageView.select()
                     .where(VisitorPageView.visitor_id == vid)
                     .order_by(VisitorPageView.created_at.desc())
                     .first())
        result.append({
            "visitor_id": vid,
            "conversation_id": conv.id if conv else None,
            "visitor_name": conv.visitor_name if conv else "Ziyaretçi",
            "current_url": last_page.url if last_page else (conv.page_url if conv else ""),
            "current_title": last_page.title if last_page else "",
            "status": conv.status if conv else "browsing",
            "connected_at": manager.live_visitors()[vid],
        })
    return result


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


# ── Forms (admin) ─────────────────────────────────────────────────────────────

def _form_summary(f: Form) -> dict:
    return {
        "id": f.id,
        "name": f.name,
        "description": f.description,
        "welcome_text": f.welcome_text,
        "submit_text": f.submit_text,
        "is_active": f.is_active,
        "department_id": getattr(f, "department_id", None),
        "field_count": FormField.select().where(FormField.form_id == f.id).count(),
        "submission_count": FormSubmission.select().where(FormSubmission.form_id == f.id).count(),
        "created_at": f.created_at.isoformat(),
    }


@router.get("/forms")
def list_forms(admin: Agent = Depends(require_permission("manage_forms"))):
    return [_form_summary(f) for f in Form.select().order_by(Form.created_at.desc())]


@router.post("/forms")
def create_form(req: FormCreate, admin: Agent = Depends(require_permission("manage_forms"))):
    f = Form.create(
        name=req.name,
        description=req.description,
        welcome_text=req.welcome_text,
        submit_text=req.submit_text,
        department_id=req.department_id,
    )
    _audit(admin.display_name or admin.username, "form_create", "form", f.id, req.name)
    return {"id": f.id, "name": f.name}


@router.patch("/forms/{form_id}")
def update_form(form_id: int, req: FormUpdate, admin: Agent = Depends(require_permission("manage_forms"))):
    f = Form.get_or_none(Form.id == form_id)
    if not f:
        raise HTTPException(404, "Form bulunamadı")
    updates: Dict[str, Any] = {}
    if req.name is not None: updates["name"] = req.name
    if req.description is not None: updates["description"] = req.description
    if req.welcome_text is not None: updates["welcome_text"] = req.welcome_text
    if req.submit_text is not None: updates["submit_text"] = req.submit_text
    if req.department_id is not None: updates["department_id"] = req.department_id
    if req.is_active is not None:
        if req.is_active:
            Form.update(is_active=False).where(Form.id != form_id).execute()
        updates["is_active"] = req.is_active
    if updates:
        Form.update(**updates).where(Form.id == form_id).execute()
    return {"ok": True}


@router.delete("/forms/{form_id}")
def delete_form(form_id: int, admin: Agent = Depends(require_permission("manage_forms"))):
    Form.delete().where(Form.id == form_id).execute()
    _audit(admin.display_name or admin.username, "form_delete", "form", form_id)
    return {"ok": True}


@router.get("/forms/{form_id}/fields")
def list_form_fields(form_id: int, admin: Agent = Depends(require_permission("manage_forms"))):
    fields = (FormField.select()
              .where(FormField.form_id == form_id)
              .order_by(FormField.order, FormField.id))
    return [
        {
            "id": ff.id, "order": ff.order, "label": ff.label,
            "field_type": ff.field_type, "required": ff.required,
            "placeholder": ff.placeholder, "options_json": ff.options_json,
        }
        for ff in fields
    ]


@router.post("/forms/{form_id}/fields")
def add_form_field(form_id: int, req: FormFieldCreate, admin: Agent = Depends(require_permission("manage_forms"))):
    if not Form.get_or_none(Form.id == form_id):
        raise HTTPException(404, "Form bulunamadı")
    max_order = FormField.select().where(FormField.form_id == form_id).count()
    ff = FormField.create(
        form_id=form_id,
        label=req.label,
        field_type=req.field_type,
        required=req.required,
        placeholder=req.placeholder,
        options_json=req.options_json,
        order=req.order if req.order else max_order,
    )
    return {"id": ff.id, "label": ff.label}


@router.patch("/forms/{form_id}/fields/{field_id}")
def update_form_field(form_id: int, field_id: int, req: FormFieldUpdate, admin: Agent = Depends(require_permission("manage_forms"))):
    ff = FormField.get_or_none(FormField.id == field_id, FormField.form_id == form_id)
    if not ff:
        raise HTTPException(404, "Alan bulunamadı")
    updates: Dict[str, Any] = {}
    if req.label is not None: updates["label"] = req.label
    if req.field_type is not None: updates["field_type"] = req.field_type
    if req.required is not None: updates["required"] = req.required
    if req.placeholder is not None: updates["placeholder"] = req.placeholder
    if req.options_json is not None: updates["options_json"] = req.options_json
    if req.order is not None: updates["order"] = req.order
    if updates:
        FormField.update(**updates).where(FormField.id == field_id).execute()
    return {"ok": True}


@router.delete("/forms/{form_id}/fields/{field_id}")
def delete_form_field(form_id: int, field_id: int, admin: Agent = Depends(require_permission("manage_forms"))):
    FormField.delete().where(FormField.id == field_id, FormField.form_id == form_id).execute()
    return {"ok": True}


@router.put("/forms/{form_id}/fields/order")
def reorder_form_fields(form_id: int, req: FieldOrderRequest, admin: Agent = Depends(require_permission("manage_forms"))):
    for i, fid in enumerate(req.field_ids):
        FormField.update(order=i).where(FormField.id == fid, FormField.form_id == form_id).execute()
    return {"ok": True}


@router.get("/forms/{form_id}/submissions")
def list_form_submissions(form_id: int, admin: Agent = Depends(require_permission("manage_forms"))):
    subs = (FormSubmission.select()
            .where(FormSubmission.form_id == form_id)
            .order_by(FormSubmission.submitted_at.desc())
            .limit(200))
    fields = list(FormField.select().where(FormField.form_id == form_id).order_by(FormField.order))
    label_map = {str(ff.id): ff.label for ff in fields}
    result = []
    for s in subs:
        try:
            answers = json.loads(s.answers_json)
        except Exception:
            answers = {}
        result.append({
            "id": s.id,
            "visitor_id": s.visitor_id,
            "conversation_id": getattr(s, "conversation_id", None),
            "answers": answers,
            "field_labels": label_map,
            "submitted_at": s.submitted_at.isoformat(),
        })
    return result
