"""Admin endpoints for the visitor-facing cookie consent platform:
an on/off toggle, notice-only vs. require-consent mode, bilingual notice text,
multiple policy links, consent button labels, full CRUD + ordering over cookie
categories and individual cookie definitions, and a consent audit log."""
from __future__ import annotations
import json
import re
from datetime import datetime
from fastapi import Depends, HTTPException

from ...database import Agent, CookieDefinition, CookieCategory, CookieConsentLog, Setting
from ...auth import require_permission
from ._base import router, _audit
from ._schemas import (
    CookieNoticeSettingsUpdate, CookieDefCreate, CookieDefUpdate,
    CookieCategoryCreate, CookieCategoryUpdate, CookieReorder,
)

_SETTING_KEYS = (
    "cookie_notice_enabled", "cookie_consent_mode",
    "cookie_notice_text", "cookie_notice_text_tr", "cookie_notice_text_en",
    "cookie_policy_url", "cookie_policy_label", "cookie_links_json",
    "cookie_accept_label", "cookie_reject_label", "cookie_customize_label",
    "cookie_save_label", "cookie_banner_position",
)


def _slugify(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (value or "").strip().lower()).strip("_")
    return s or "category"


def _get_setting_rows() -> dict:
    return {s.key: s.value for s in Setting.select().where(Setting.key.in_(_SETTING_KEYS))}


def _save_settings(data: dict):
    for key, value in data.items():
        (Setting.insert(key=key, value=str(value), updated_at=datetime.utcnow())
         .on_conflict(conflict_target=[Setting.key],
                      update={Setting.value: str(value), Setting.updated_at: datetime.utcnow()})
         .execute())
    from ...settings_cache import invalidate as _invalidate_settings
    _invalidate_settings()


def _parse_links(raw: str, fallback_url: str = "", fallback_label: str = "") -> list:
    try:
        links = json.loads(raw or "[]")
        if not isinstance(links, list):
            links = []
    except Exception:
        links = []
    links = [{"label": str(l.get("label", "")), "url": str(l.get("url", ""))}
             for l in links if isinstance(l, dict) and l.get("url")]
    if not links and fallback_url:
        links = [{"label": fallback_label or "", "url": fallback_url}]
    return links


def _cookie_def_dict(c: CookieDefinition) -> dict:
    return {
        "id": c.id, "name": c.name, "description": c.description,
        "is_mandatory": c.is_mandatory, "category_key": getattr(c, "category_key", "necessary"),
        "provider": getattr(c, "provider", ""), "duration": getattr(c, "duration", ""),
        "order": c.order, "created_at": c.created_at.isoformat(),
    }


def _category_dict(c: CookieCategory) -> dict:
    return {
        "id": c.id, "key": c.key, "name": c.name, "description": c.description,
        "is_required": c.is_required, "order": c.order, "created_at": c.created_at.isoformat(),
    }


# ── Notice / consent settings ──────────────────────────────────────────────────

@router.get("/cookies/settings")
def get_cookie_settings(admin: Agent = Depends(require_permission("manage_settings"))):
    rows = _get_setting_rows()
    return {
        "enabled": rows.get("cookie_notice_enabled", "true") != "false",
        "consent_mode": rows.get("cookie_consent_mode", "notice"),
        "text": rows.get("cookie_notice_text", ""),
        "text_tr": rows.get("cookie_notice_text_tr", ""),
        "text_en": rows.get("cookie_notice_text_en", ""),
        "policy_url": rows.get("cookie_policy_url", ""),
        "policy_label": rows.get("cookie_policy_label", ""),
        "links": _parse_links(rows.get("cookie_links_json", ""),
                              rows.get("cookie_policy_url", ""), rows.get("cookie_policy_label", "")),
        "accept_label": rows.get("cookie_accept_label", ""),
        "reject_label": rows.get("cookie_reject_label", ""),
        "customize_label": rows.get("cookie_customize_label", ""),
        "save_label": rows.get("cookie_save_label", ""),
        "banner_position": rows.get("cookie_banner_position", "bottom"),
    }


@router.put("/cookies/settings")
def update_cookie_settings(req: CookieNoticeSettingsUpdate, admin: Agent = Depends(require_permission("manage_settings"))):
    data = {}
    if req.enabled is not None:
        data["cookie_notice_enabled"] = "true" if req.enabled else "false"
    if req.consent_mode is not None:
        data["cookie_consent_mode"] = "consent" if req.consent_mode == "consent" else "notice"
    if req.text is not None:
        data["cookie_notice_text"] = req.text
    if req.text_tr is not None:
        data["cookie_notice_text_tr"] = req.text_tr
    if req.text_en is not None:
        data["cookie_notice_text_en"] = req.text_en
    if req.policy_url is not None:
        data["cookie_policy_url"] = req.policy_url
    if req.policy_label is not None:
        data["cookie_policy_label"] = req.policy_label
    if req.links is not None:
        clean = [{"label": str(l.get("label", "")).strip(), "url": str(l.get("url", "")).strip()}
                 for l in req.links if isinstance(l, dict) and str(l.get("url", "")).strip()]
        data["cookie_links_json"] = json.dumps(clean, ensure_ascii=False)
    if req.accept_label is not None:
        data["cookie_accept_label"] = req.accept_label
    if req.reject_label is not None:
        data["cookie_reject_label"] = req.reject_label
    if req.customize_label is not None:
        data["cookie_customize_label"] = req.customize_label
    if req.save_label is not None:
        data["cookie_save_label"] = req.save_label
    if req.banner_position is not None:
        data["cookie_banner_position"] = "corner" if req.banner_position == "corner" else "bottom"
    _save_settings(data)
    _audit(admin.display_name or admin.username, "cookie_settings_update", "settings", None, "")
    return {"ok": True}


# ── Cookie categories ──────────────────────────────────────────────────────────

@router.get("/cookie-categories")
def list_cookie_categories(admin: Agent = Depends(require_permission("manage_settings"))):
    return [_category_dict(c) for c in CookieCategory.select().order_by(CookieCategory.order, CookieCategory.id)]


@router.post("/cookie-categories")
def create_cookie_category(req: CookieCategoryCreate, admin: Agent = Depends(require_permission("manage_settings"))):
    name = req.name.strip()
    if not name:
        raise HTTPException(400, "Kategori adı gerekli")
    key = _slugify(req.key or name)
    base, i = key, 2
    while CookieCategory.get_or_none(CookieCategory.key == key):
        key = f"{base}_{i}"; i += 1
    order = CookieCategory.select().count()
    c = CookieCategory.create(key=key, name=name, description=req.description, is_required=req.is_required, order=order)
    _audit(admin.display_name or admin.username, "cookie_category_create", "cookie_category", c.id, name)
    return _category_dict(c)


@router.patch("/cookie-categories/{cat_id}")
def update_cookie_category(cat_id: int, req: CookieCategoryUpdate, admin: Agent = Depends(require_permission("manage_settings"))):
    c = CookieCategory.get_or_none(CookieCategory.id == cat_id)
    if not c:
        raise HTTPException(404, "Kategori bulunamadı")
    updates = {}
    if req.name is not None and req.name.strip():
        updates["name"] = req.name.strip()
    if req.description is not None:
        updates["description"] = req.description
    if req.is_required is not None:
        updates["is_required"] = req.is_required
    if updates:
        CookieCategory.update(**updates).where(CookieCategory.id == cat_id).execute()
        c = CookieCategory.get_by_id(cat_id)
    return _category_dict(c)


@router.delete("/cookie-categories/{cat_id}")
def delete_cookie_category(cat_id: int, admin: Agent = Depends(require_permission("manage_settings"))):
    c = CookieCategory.get_or_none(CookieCategory.id == cat_id)
    if not c:
        raise HTTPException(404, "Kategori bulunamadı")
    # Reassign any cookies in this category back to "necessary" so nothing is orphaned.
    CookieDefinition.update(category_key="necessary").where(CookieDefinition.category_key == c.key).execute()
    name = c.name
    CookieCategory.delete().where(CookieCategory.id == cat_id).execute()
    _audit(admin.display_name or admin.username, "cookie_category_delete", "cookie_category", cat_id, name)
    return {"ok": True}


@router.post("/cookie-categories/reorder")
def reorder_cookie_categories(req: CookieReorder, admin: Agent = Depends(require_permission("manage_settings"))):
    for idx, cid in enumerate(req.ids):
        CookieCategory.update(order=idx).where(CookieCategory.id == cid).execute()
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
    order = CookieDefinition.select().count()
    c = CookieDefinition.create(
        name=name, description=req.description, is_mandatory=req.is_mandatory,
        category_key=req.category_key or "necessary", provider=req.provider,
        duration=req.duration, order=order,
    )
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
    if req.category_key is not None:
        updates["category_key"] = req.category_key
    if req.provider is not None:
        updates["provider"] = req.provider
    if req.duration is not None:
        updates["duration"] = req.duration
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


@router.post("/cookies/reorder")
def reorder_cookie_defs(req: CookieReorder, admin: Agent = Depends(require_permission("manage_settings"))):
    for idx, cid in enumerate(req.ids):
        CookieDefinition.update(order=idx).where(CookieDefinition.id == cid).execute()
    return {"ok": True}


# ── Consent audit log ──────────────────────────────────────────────────────────

@router.get("/cookie-consents")
def list_cookie_consents(admin: Agent = Depends(require_permission("manage_settings"))):
    rows = CookieConsentLog.select().order_by(CookieConsentLog.created_at.desc()).limit(200)
    out = []
    for r in rows:
        try:
            choices = json.loads(r.choices_json or "{}")
        except Exception:
            choices = {}
        out.append({
            "id": r.id, "visitor_id": r.visitor_id, "choices": choices,
            "accepted_categories": r.accepted_categories, "ip_address": r.ip_address,
            "user_agent": r.user_agent, "created_at": r.created_at.isoformat(),
        })
    return out


@router.delete("/cookie-consents")
def clear_cookie_consents(admin: Agent = Depends(require_permission("manage_settings"))):
    n = CookieConsentLog.delete().execute()
    _audit(admin.display_name or admin.username, "cookie_consents_clear", "cookie_consent", None, f"{n} kayıt")
    return {"ok": True, "deleted": n}
