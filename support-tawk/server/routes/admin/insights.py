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
    database,
    Department, Agent, Conversation, Message, CannedResponse,
    Tag, ConversationTag, BlacklistedIP, BanAppeal, Rating, WorkSchedule, Bot, BotRule, Setting,
    Note, WebhookConfig, VisitorPageView, VisitorField, AuditLog, OfflineMessage,
    Form, FormField, FormSubmission, DeletedVisitorArchive, ARCHIVE_RETENTION_DAYS,
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

from ._base import router, _audit, _conv_summary
from ._schemas import *  # noqa: F401,F403  (request models)


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

@router.get("/visitors/{visitor_id}/forms")
def visitor_form_submissions(visitor_id: str, agent: Agent = Depends(get_current_agent)):
    """Every form this visitor submitted, with answers mapped to field labels."""
    subs = (FormSubmission.select()
            .where(FormSubmission.visitor_id == visitor_id)
            .order_by(FormSubmission.submitted_at.desc())
            .limit(50))
    out = []
    for s in subs:
        form = Form.get_or_none(Form.id == s.form_id)
        labels = {}
        if form:
            for ff in form.fields:
                labels[str(ff.id)] = ff.label
        try:
            answers = json.loads(s.answers_json or "{}")
        except Exception:
            answers = {}
        out.append({
            "id": s.id,
            "form_name": form.name if form else "Form",
            "submitted_at": s.submitted_at.isoformat(),
            "answers": [{"label": labels.get(str(k), str(k)), "value": v} for k, v in answers.items()],
        })
    return out


@router.get("/visitors/search")
def search_visitors(q: str = "", admin: Agent = Depends(get_current_agent)):
    """Find visitors by id, name or email. Name/email are encrypted at rest, so
    we decrypt-and-match in Python over the most recent conversations."""
    needle = (q or "").strip().lower()
    results: dict[str, dict] = {}
    convs = Conversation.select().order_by(Conversation.updated_at.desc()).limit(500)
    for c in convs:
        vid = c.visitor_id or ""
        hay = " ".join([vid, c.visitor_name or "", c.visitor_email or ""]).lower()
        if needle and needle not in hay:
            continue
        r = results.get(vid)
        if not r:
            r = results[vid] = {
                "visitor_id": vid,
                "visitor_name": c.visitor_name,
                "visitor_email": c.visitor_email,
                "last_seen": c.updated_at.isoformat(),
                "conversation_count": 0,
            }
        r["conversation_count"] += 1
    out = sorted(results.values(), key=lambda x: x["last_seen"], reverse=True)
    return out[:100]


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


# ── Visitor data deletion with a recoverable archive window ────────────────────

def _dt(s):
    """Parse an isoformat string back to datetime, falling back to 'now'."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.utcnow()


def _purge_expired_archives():
    cutoff = datetime.utcnow() - timedelta(days=ARCHIVE_RETENTION_DAYS)
    DeletedVisitorArchive.delete().where(DeletedVisitorArchive.deleted_at < cutoff).execute()


def _snapshot_visitor(visitor_id: str):
    """Serialize every row tied to a visitor into a plain dict + a row count."""
    count = 0
    conv_snaps = []
    for c in Conversation.select().where(Conversation.visitor_id == visitor_id):
        count += 1
        msgs = []
        for m in Message.select().where(Message.conversation == c):
            count += 1
            msgs.append({
                "sender_type": m.sender_type, "sender_id": m.sender_id,
                "sender_name": m.sender_name, "content": m.content,
                "file_url": m.file_url, "file_name": m.file_name,
                "file_size": m.file_size, "is_read": m.is_read,
                "created_at": m.created_at.isoformat(),
            })
        notes = []
        for n in Note.select().where(Note.conversation == c):
            count += 1
            notes.append({
                "agent_id": n.agent_id, "agent_name": n.agent_name,
                "content": n.content, "created_at": n.created_at.isoformat(),
            })
        rating = None
        r = Rating.get_or_none(Rating.conversation == c)
        if r:
            count += 1
            rating = {"score": r.score, "comment": r.comment, "created_at": r.created_at.isoformat()}
        tag_ids = [ct.tag_id for ct in ConversationTag.select().where(ConversationTag.conversation == c)]
        count += len(tag_ids)
        fsubs = []
        for s in FormSubmission.select().where(FormSubmission.conversation == c):
            count += 1
            fsubs.append({"form_id": s.form_id, "answers_json": s.answers_json,
                          "submitted_at": s.submitted_at.isoformat()})
        conv_snaps.append({
            "visitor_name": c.visitor_name, "visitor_email": c.visitor_email,
            "status": c.status, "site_name": c.site_name, "page_url": c.page_url,
            "created_at": c.created_at.isoformat(), "updated_at": c.updated_at.isoformat(),
            "closed_at": c.closed_at.isoformat() if c.closed_at else None,
            "ip_address": c.ip_address, "user_agent": c.user_agent,
            "country": c.country, "city": c.city, "language": c.language,
            "priority": c.priority, "department_id": c.department_id,
            "assigned_to_id": c.assigned_to_id,
            "messages": msgs, "notes": notes, "rating": rating,
            "tag_ids": tag_ids, "form_submissions": fsubs,
        })

    fields = []
    for f in VisitorField.select().where(VisitorField.visitor_id == visitor_id):
        count += 1
        fields.append({"key": f.key, "value": f.value})

    pages = []
    for p in VisitorPageView.select().where(VisitorPageView.visitor_id == visitor_id):
        count += 1
        pages.append({"url": p.url, "title": p.title, "created_at": p.created_at.isoformat()})

    offline = []
    for o in OfflineMessage.select().where(OfflineMessage.visitor_id == visitor_id):
        count += 1
        offline.append({
            "visitor_name": o.visitor_name, "visitor_email": o.visitor_email,
            "message": o.message, "page_url": o.page_url, "is_read": o.is_read,
            "created_at": o.created_at.isoformat(),
        })

    loose_subs = []
    for s in FormSubmission.select().where(
            FormSubmission.visitor_id == visitor_id,
            FormSubmission.conversation.is_null(True)):
        count += 1
        loose_subs.append({"form_id": s.form_id, "answers_json": s.answers_json,
                           "submitted_at": s.submitted_at.isoformat()})

    return {
        "conversations": conv_snaps, "fields": fields, "pages": pages,
        "offline_messages": offline, "form_submissions": loose_subs,
    }, count


def _restore_visitor(visitor_id: str, payload: dict):
    """Re-create rows from a snapshot. FKs to entities that no longer exist
    (deleted departments/agents/tags/forms) are dropped or skipped gracefully."""
    for cs in payload.get("conversations", []):
        dept_id = cs.get("department_id")
        if dept_id and not Department.get_or_none(Department.id == dept_id):
            dept_id = None
        agent_id = cs.get("assigned_to_id")
        if agent_id and not Agent.get_or_none(Agent.id == agent_id):
            agent_id = None
        conv = Conversation.create(
            visitor_id=visitor_id, visitor_name=cs.get("visitor_name", ""),
            visitor_email=cs.get("visitor_email", ""), status=cs.get("status", "closed"),
            site_name=cs.get("site_name", ""), page_url=cs.get("page_url", ""),
            created_at=_dt(cs.get("created_at")) or datetime.utcnow(),
            updated_at=_dt(cs.get("updated_at")) or datetime.utcnow(),
            closed_at=_dt(cs.get("closed_at")),
            ip_address=cs.get("ip_address", ""), user_agent=cs.get("user_agent", ""),
            country=cs.get("country", ""), city=cs.get("city", ""),
            language=cs.get("language", ""), priority=cs.get("priority", "normal"),
            department=dept_id, assigned_to=agent_id,
        )
        for m in cs.get("messages", []):
            Message.create(
                conversation=conv, sender_type=m.get("sender_type", "visitor"),
                sender_id=m.get("sender_id", ""), sender_name=m.get("sender_name", ""),
                content=m.get("content", ""), file_url=m.get("file_url", ""),
                file_name=m.get("file_name", ""), file_size=m.get("file_size", 0),
                is_read=m.get("is_read", False),
                created_at=_dt(m.get("created_at")) or datetime.utcnow(),
            )
        for n in cs.get("notes", []):
            aid = n.get("agent_id")
            if aid and not Agent.get_or_none(Agent.id == aid):
                aid = None
            Note.create(conversation=conv, agent=aid, agent_name=n.get("agent_name", ""),
                        content=n.get("content", ""),
                        created_at=_dt(n.get("created_at")) or datetime.utcnow())
        if cs.get("rating"):
            rr = cs["rating"]
            Rating.create(conversation=conv, score=rr.get("score", 0),
                          comment=rr.get("comment", ""),
                          created_at=_dt(rr.get("created_at")) or datetime.utcnow())
        for tid in cs.get("tag_ids", []):
            if Tag.get_or_none(Tag.id == tid):
                try:
                    ConversationTag.create(conversation=conv, tag=tid)
                except Exception:
                    pass
        for s in cs.get("form_submissions", []):
            if Form.get_or_none(Form.id == s.get("form_id")):
                FormSubmission.create(form=s["form_id"], conversation=conv,
                                      visitor_id=visitor_id,
                                      answers_json=s.get("answers_json", "{}"),
                                      submitted_at=_dt(s.get("submitted_at")) or datetime.utcnow())

    for f in payload.get("fields", []):
        (VisitorField.insert(visitor_id=visitor_id, key=f.get("key", ""), value=f.get("value", ""))
         .on_conflict(conflict_target=[VisitorField.visitor_id, VisitorField.key],
                      update={VisitorField.value: f.get("value", "")})
         .execute())

    for p in payload.get("pages", []):
        VisitorPageView.create(visitor_id=visitor_id, url=p.get("url", ""),
                               title=p.get("title", ""),
                               created_at=_dt(p.get("created_at")) or datetime.utcnow())

    for o in payload.get("offline_messages", []):
        OfflineMessage.create(visitor_id=visitor_id, visitor_name=o.get("visitor_name", ""),
                              visitor_email=o.get("visitor_email", ""),
                              message=o.get("message", ""), page_url=o.get("page_url", ""),
                              is_read=o.get("is_read", False),
                              created_at=_dt(o.get("created_at")) or datetime.utcnow())

    for s in payload.get("form_submissions", []):
        if Form.get_or_none(Form.id == s.get("form_id")):
            FormSubmission.create(form=s["form_id"], conversation=None,
                                  visitor_id=visitor_id,
                                  answers_json=s.get("answers_json", "{}"),
                                  submitted_at=_dt(s.get("submitted_at")) or datetime.utcnow())


@router.delete("/visitors/{visitor_id}/data")
def delete_visitor_data(visitor_id: str, admin: Agent = Depends(require_permission("delete_data"))):
    # Snapshot first so an accidental wipe can be undone within the retention window.
    snapshot, count = _snapshot_visitor(visitor_id)
    if count > 0:
        DeletedVisitorArchive.create(
            visitor_id=visitor_id,
            payload_json=json.dumps(snapshot, ensure_ascii=False),
            item_count=count,
            deleted_by=admin.display_name or admin.username,
        )
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
    _purge_expired_archives()
    _audit(admin.display_name or admin.username, "delete_visitor_data", "visitor", None,
           f"{visitor_id} ({count} satır arşivlendi)")
    return {"ok": True, "archived_items": count}


@router.get("/deleted-visitors")
def list_deleted_visitors(admin: Agent = Depends(require_permission("delete_data"))):
    _purge_expired_archives()
    out = []
    for a in DeletedVisitorArchive.select().order_by(DeletedVisitorArchive.deleted_at.desc()):
        out.append({
            "id": a.id, "visitor_id": a.visitor_id, "item_count": a.item_count,
            "deleted_by": a.deleted_by, "deleted_at": a.deleted_at.isoformat(),
            "expires_at": (a.deleted_at + timedelta(days=ARCHIVE_RETENTION_DAYS)).isoformat(),
        })
    return out


@router.post("/deleted-visitors/{archive_id}/restore")
def restore_deleted_visitor(archive_id: int, admin: Agent = Depends(require_permission("delete_data"))):
    a = DeletedVisitorArchive.get_or_none(DeletedVisitorArchive.id == archive_id)
    if not a:
        raise HTTPException(status_code=404, detail="Arşiv kaydı bulunamadı")
    try:
        payload = json.loads(a.payload_json or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="Arşiv verisi okunamadı")
    with database.atomic():
        _restore_visitor(a.visitor_id, payload)
    vid = a.visitor_id
    a.delete_instance()
    _audit(admin.display_name or admin.username, "restore_visitor_data", "visitor", None, vid)
    return {"ok": True}


@router.delete("/deleted-visitors/{archive_id}")
def purge_deleted_visitor(archive_id: int, admin: Agent = Depends(require_permission("delete_data"))):
    a = DeletedVisitorArchive.get_or_none(DeletedVisitorArchive.id == archive_id)
    if not a:
        raise HTTPException(status_code=404, detail="Arşiv kaydı bulunamadı")
    vid = a.visitor_id
    a.delete_instance()
    _audit(admin.display_name or admin.username, "purge_visitor_archive", "visitor", None, vid)
    return {"ok": True}


# ── Live visitors ─────────────────────────────────────────────────────────────

@router.get("/live-visitors")
def live_visitors(agent: Agent = Depends(get_current_agent)):
    from ...ws_manager import manager
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


