from __future__ import annotations
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..database import Form, FormField, FormSubmission, Conversation, Message

router = APIRouter(prefix="/api")


def _public_form(form: Form) -> dict:
    fields = []
    for f in (FormField.select()
              .where(FormField.form_id == form.id)
              .order_by(FormField.order, FormField.id)):
        try:
            options = json.loads(f.options_json or "[]")
        except Exception:
            options = []
        fields.append({
            "id": f.id,
            "order": f.order,
            "label": f.label,
            "field_type": f.field_type,
            "required": f.required,
            "placeholder": f.placeholder,
            "options": options,
        })
    return {
        "id": form.id,
        "name": form.name,
        "description": form.description,
        "welcome_text": form.welcome_text,
        "submit_text": form.submit_text,
        "fields": fields,
    }


@router.get("/form")
def get_active_form():
    form = Form.get_or_none(Form.is_active == True)
    if not form:
        return None
    return _public_form(form)


class FormSubmitRequest(BaseModel):
    form_id: int
    visitor_id: str
    conversation_id: Optional[int] = None
    answers: dict  # {field_id_str: value_str}


@router.post("/form/submit")
async def submit_form(req: FormSubmitRequest):
    form = Form.get_or_none(Form.id == req.form_id)
    if not form:
        raise HTTPException(404, "Form bulunamadı")

    sub = FormSubmission.create(
        form_id=form.id,
        conversation_id=req.conversation_id,
        visitor_id=req.visitor_id,
        answers_json=json.dumps(req.answers, ensure_ascii=False),
        submitted_at=datetime.utcnow(),
    )

    # Build formatted summary for the chat
    fields = list(FormField.select()
                  .where(FormField.form_id == form.id)
                  .order_by(FormField.order, FormField.id))
    lines = ["📋 **" + form.name + "** — Form Yanıtları\n"]
    for f in fields:
        answer = req.answers.get(str(f.id), "")
        if answer:
            lines.append("**" + f.label + ":** " + str(answer))
    summary = "\n".join(lines)

    if req.conversation_id:
        conv = Conversation.get_or_none(Conversation.id == req.conversation_id)
        if conv:
            msg = Message.create(
                conversation_id=conv.id,
                sender_type="system",
                sender_id="form",
                sender_name="Form",
                content=summary,
                created_at=datetime.utcnow(),
            )
            updates = {"updated_at": datetime.utcnow()}
            if getattr(form, "department_id", None):
                updates["department_id"] = form.department_id
            Conversation.update(**updates).where(Conversation.id == conv.id).execute()

            from ..ws_manager import manager
            await manager.broadcast_to_agents({
                "type": "message",
                "conversation_id": conv.id,
                "message": {
                    "id": msg.id,
                    "sender_type": "system",
                    "sender_name": "Form",
                    "content": summary,
                    "created_at": msg.created_at.isoformat(),
                },
            })

    return {"ok": True, "submission_id": sub.id}
