"""Admin endpoints for the visitor-facing cookie notice: an on/off toggle,
custom notice text and policy link, and full CRUD over the individual
cookie/storage entries shown to visitors (name, description, mandatory flag)."""
from __future__ import annotations
from datetime import datetime
from fastapi import Depends, HTTPException

from ...database import Agent, CookieDefinition, Setting
from ...auth import require_permission
from ._base import router, _audit
from ._schemas import CookieNoticeSettingsUpdate, CookieDefCreate, CookieDefUpdate

_SETTING_KEYS = ("cookie_notice_enabled", "cookie_notice_text", "cookie_policy_url", "cookie_policy_label")


def _cookie_def_dict(c: CookieDefinition) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "is_mandatory": c.is_mandatory,
        "order": c.order,
        "created_at": c.created_at.isoformat(),
    }


# ── Notice settings (enabled toggle, text, policy link) ───────────────────────

@router.get("/cookies/settings")
def get_cookie_settings(admin: Agent = Depends(require_permission("manage_settings"))):
    rows = {s.key: s.value for s in Setting.select().where(Setting.key.in_(_SETTING_KEYS))}
    return {
        "enabled": rows.get("cookie_notice_enabled", "true") != "false",
        "text": rows.get("cookie_notice_text", ""),
        "policy_url": rows.get("cookie_policy_url", ""),
        "policy_label": rows.get("cookie_policy_label", ""),
    }


@router.put("/cookies/settings")
def update_cookie_settings(req: CookieNoticeSettingsUpdate, admin: Agent = Depends(require_permission("manage_settings"))):
    data = {}
    if req.enabled is not None:
        data["cookie_notice_enabled"] = "true" if req.enabled else "false"
    if req.text is not None:
        data["cookie_notice_text"] = req.text
    if req.policy_url is not None:
        data["cookie_policy_url"] = req.policy_url
    if req.policy_label is not None:
        data["cookie_policy_label"] = req.policy_label
    for key, value in data.items():
        (Setting.insert(key=key, value=str(value), updated_at=datetime.utcnow())
         .on_conflict(conflict_target=[Setting.key],
                      update={Setting.value: str(value), Setting.updated_at: datetime.utcnow()})
         .execute())
    from ...settings_cache import invalidate as _invalidate_settings
    _invalidate_settings()
    _audit(admin.display_name or admin.username, "cookie_settings_update", "settings", None, "")
    return {"ok": True}


# ── Individual cookie/storage definitions ──────────────────────────────────────

@router.get("/cookies")
def list_cookie_defs(admin: Agent = Depends(require_permission("manage_settings"))):
    return [_cookie_def_dict(c) for c in CookieDefinition.select().order_by(CookieDefinition.order, CookieDefinition.created_at)]


@router.post("/cookies")
def create_cookie_def(req: CookieDefCreate, admin: Agent = Depends(require_permission("manage_settings"))):
    name = req.name.strip()
    if not name:
        raise HTTPException(400, "Çerez adı gerekli")
    order = (CookieDefinition.select().count())
    c = CookieDefinition.create(name=name, description=req.description, is_mandatory=req.is_mandatory, order=order)
    _audit(admin.display_name or admin.username, "cookie_def_create", "cookie", c.id, name)
    return _cookie_def_dict(c)


@router.patch("/cookies/{cookie_id}")
def update_cookie_def(cookie_id: int, req: CookieDefUpdate, admin: Agent = Depends(require_permission("manage_settings"))):
    c = CookieDefinition.get_or_none(CookieDefinition.id == cookie_id)
    if not c:
        raise HTTPException(404, "Çerez tanımı bulunamadı")
    updates = {}
    if req.name is not None and req.name.strip():
        updates["name"] = req.name.strip()
    if req.description is not None:
        updates["description"] = req.description
    if req.is_mandatory is not None:
        updates["is_mandatory"] = req.is_mandatory
    if updates:
        CookieDefinition.update(**updates).where(CookieDefinition.id == cookie_id).execute()
        c = CookieDefinition.get_by_id(cookie_id)
    return _cookie_def_dict(c)


@router.delete("/cookies/{cookie_id}")
def delete_cookie_def(cookie_id: int, admin: Agent = Depends(require_permission("manage_settings"))):
    c = CookieDefinition.get_or_none(CookieDefinition.id == cookie_id)
    if not c:
        raise HTTPException(404, "Çerez tanımı bulunamadı")
    name = c.name
    CookieDefinition.delete().where(CookieDefinition.id == cookie_id).execute()
    _audit(admin.display_name or admin.username, "cookie_def_delete", "cookie", cookie_id, name)
    return {"ok": True}
