"""Pydantic request/response schemas shared across admin route modules."""
from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


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


class BotCreate(BaseModel):
    name: str = "Bot"
    greeting: str = "Merhaba! Size nasıl yardımcı olabilirim?"
    options_json: str = "[]"
    similarity_threshold: Optional[int] = None
    priority: int = 0


class BotUpdate(BaseModel):
    name: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    greeting: Optional[str] = None
    options_json: Optional[str] = None
    similarity_threshold: Optional[int] = None
    priority: Optional[int] = None


class BotRuleCreate(BaseModel):
    triggers_json: str = "[]"
    reply: str = ""
    department_id: Optional[int] = None
    is_enabled: bool = True


class BotRuleUpdate(BaseModel):
    triggers_json: Optional[str] = None
    reply: Optional[str] = None
    department_id: Optional[int] = None
    is_enabled: Optional[bool] = None


class BotSettingsUpdate(BaseModel):
    default_threshold: int


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


class CookieNoticeSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    consent_mode: Optional[str] = None         # "notice" | "consent"
    text: Optional[str] = None                 # legacy single-language text
    text_tr: Optional[str] = None
    text_en: Optional[str] = None
    policy_url: Optional[str] = None           # legacy single link
    policy_label: Optional[str] = None
    links: Optional[List[Dict[str, Any]]] = None   # [{label, url}, ...]
    accept_label: Optional[str] = None
    reject_label: Optional[str] = None
    customize_label: Optional[str] = None
    save_label: Optional[str] = None
    banner_position: Optional[str] = None      # "bottom" | "corner"


class CookieDefCreate(BaseModel):
    name: str
    description: str = ""
    is_mandatory: bool = False
    category_key: str = "necessary"
    provider: str = ""
    duration: str = ""


class CookieDefUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_mandatory: Optional[bool] = None
    category_key: Optional[str] = None
    provider: Optional[str] = None
    duration: Optional[str] = None


class CookieCategoryCreate(BaseModel):
    key: Optional[str] = None
    name: str
    description: str = ""
    is_required: bool = False


class CookieCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_required: Optional[bool] = None


class CookieReorder(BaseModel):
    ids: List[int]

