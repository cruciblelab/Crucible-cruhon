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


