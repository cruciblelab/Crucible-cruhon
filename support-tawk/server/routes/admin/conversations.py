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

from ._base import router, _audit, _conv_full, _conv_summary, _msg_dict
from ._schemas import *  # noqa: F401,F403  (request models)


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
                from ...database import Tag, ConversationTag
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


