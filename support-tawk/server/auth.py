from __future__ import annotations
import json
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import config
from .database import Agent

_SECRET = config.server.secret_key
_HOURS = config.admin.session_hours
_bearer = HTTPBearer(auto_error=False)

# ── Yetki (Permission) kataloğu ───────────────────────────────────────────────
# Her yetki: anahtar → (etiket, açıklama). "admin" rolü tüm yetkilere sahiptir.
PERMISSIONS = [
    {"key": "manage_agents",      "label": "Temsilci & Rol Yönetimi", "desc": "Temsilci ekleme/silme, yetki verme"},
    {"key": "manage_blacklist",   "label": "Kara Liste & Banlama",    "desc": "IP/ziyaretçi engelleme ve kaldırma"},
    {"key": "manage_departments", "label": "Departman Yönetimi",       "desc": "Departman oluşturma ve atama"},
    {"key": "manage_settings",    "label": "Site Ayarları",            "desc": "Widget, dil, görünüm ayarları"},
    {"key": "manage_forms",       "label": "Form Yönetimi",            "desc": "Form oluşturma ve düzenleme"},
    {"key": "manage_botflow",     "label": "Bot Akışları",             "desc": "Otomatik bot akışlarını yönetme"},
    {"key": "manage_tags",        "label": "Etiket Yönetimi",          "desc": "Etiket oluşturma/silme"},
    {"key": "manage_webhooks",    "label": "Webhook Yönetimi",         "desc": "Webhook/entegrasyon ayarları"},
    {"key": "manage_schedule",    "label": "Mesai Saatleri",           "desc": "Temsilci mesai saatlerini ayarlama"},
    {"key": "delete_data",        "label": "Veri Silme",               "desc": "Ziyaretçi verilerini kalıcı silme"},
    {"key": "view_audit",         "label": "Denetim Logu",             "desc": "Yönetici işlem kayıtlarını görme"},
    {"key": "export_data",        "label": "Dışa Aktarma",             "desc": "CSV/Excel rapor indirme"},
]
PERMISSION_KEYS = {p["key"] for p in PERMISSIONS}


def agent_permissions(agent: Agent) -> set:
    """Bir temsilcinin sahip olduğu yetki anahtarları. Admin = tümü."""
    if agent.role == "admin":
        return set(PERMISSION_KEYS)
    try:
        perms = json.loads(agent.permissions or "[]")
        if isinstance(perms, list):
            return {p for p in perms if p in PERMISSION_KEYS}
    except Exception:
        pass
    return set()


def has_permission(agent: Agent, perm: str) -> bool:
    return perm in agent_permissions(agent)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(agent_id: int, role: str) -> str:
    payload = {
        "sub": str(agent_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=_HOURS),
    }
    return jwt.encode(payload, _SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, _SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token süresi doldu")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz token")


def get_current_agent(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> Agent:
    if not creds:
        raise HTTPException(status_code=401, detail="Kimlik doğrulama gerekli")
    payload = decode_token(creds.credentials)
    agent = Agent.get_or_none(Agent.id == int(payload["sub"]), Agent.is_active == True)
    if not agent:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    return agent


def require_admin(agent: Agent = Depends(get_current_agent)) -> Agent:
    if agent.role != "admin":
        raise HTTPException(status_code=403, detail="Yönetici yetkisi gerekli")
    return agent


def require_permission(perm: str):
    """Belirli bir yetki gerektiren endpoint'ler için dependency üretir.
    Admin rolü her zaman geçer."""
    def _dep(agent: Agent = Depends(get_current_agent)) -> Agent:
        if not has_permission(agent, perm):
            raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
        return agent
    return _dep


def verify_ws_token(token: str) -> Agent | None:
    try:
        payload = decode_token(token)
        return Agent.get_or_none(Agent.id == int(payload["sub"]), Agent.is_active == True)
    except Exception:
        return None
