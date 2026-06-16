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
