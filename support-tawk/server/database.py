from __future__ import annotations
import os
from pathlib import Path
from peewee import (
    Model, SqliteDatabase, PostgresqlDatabase, MySQLDatabase,
    CharField, TextField, IntegerField, BooleanField,
    DateTimeField, ForeignKeyField, AutoField
)
from datetime import datetime
from .config import config
from .crypto import encrypt as _encrypt, decrypt as _decrypt

db_cfg = config.database

# Performance-oriented SQLite pragmas:
#   wal           — concurrent readers don't block the single writer
#   synchronous   — NORMAL is safe under WAL and far faster than FULL
#   cache_size    — negative value = KiB; ~64MB page cache
#   busy_timeout  — wait instead of erroring when the DB is briefly locked
#   mmap_size     — memory-map up to 256MB for faster reads
#   temp_store    — keep temp tables/indexes in memory
_SQLITE_PRAGMAS = {
    "journal_mode": "wal",
    "foreign_keys": 1,
    "synchronous": 1,          # NORMAL
    "cache_size": -64000,      # ~64MB
    "busy_timeout": 5000,      # 5s
    "mmap_size": 268435456,    # 256MB
    "temp_store": 2,           # MEMORY
}


def _make_db():
    t = db_cfg.type.lower()
    if t == "sqlite":
        Path(db_cfg.path).parent.mkdir(parents=True, exist_ok=True)
        return SqliteDatabase(db_cfg.path, pragmas=_SQLITE_PRAGMAS)
    if t == "postgres":
        return PostgresqlDatabase(
            db_cfg.name, user=db_cfg.username, password=db_cfg.password,
            host=db_cfg.host, port=db_cfg.port
        )
    if t == "mysql":
        return MySQLDatabase(
            db_cfg.name, user=db_cfg.username, password=db_cfg.password,
            host=db_cfg.host, port=db_cfg.port
        )
    raise ValueError(f"Desteklenmeyen veritabanı türü: {t}")


database = _make_db()


class BaseModel(Model):
    class Meta:
        database = database


class EncryptedTextField(TextField):
    """TextField that transparently encrypts on write and decrypts on read."""
    def db_value(self, value):
        return _encrypt(value) if value is not None else None

    def python_value(self, value):
        return _decrypt(value) if value is not None else None


class EncryptedCharField(CharField):
    """CharField equivalent. Stored as TEXT-sized VARCHAR; SQLite ignores the
    length limit and the ciphertext is longer than the plaintext."""
    def db_value(self, value):
        return _encrypt(value) if value is not None else None

    def python_value(self, value):
        return _decrypt(value) if value is not None else None


class Department(BaseModel):
    id = AutoField()
    name = CharField(max_length=64, unique=True)
    description = CharField(max_length=256, default="")
    color = CharField(max_length=20, default="#6366f1")
    icon = CharField(max_length=8, default="💼")
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "departments"


class Agent(BaseModel):
    id = AutoField()
    username = CharField(unique=True, max_length=64)
    password_hash = CharField(max_length=256)
    display_name = CharField(max_length=128, default="")
    role = CharField(max_length=16, default="agent")  # admin | agent
    permissions = TextField(default="[]")  # JSON list of permission keys (admin = hepsi)
    is_active = BooleanField(default=True)
    is_online = BooleanField(default=False)
    avatar_color = CharField(max_length=20, default="#6366f1")
    department = ForeignKeyField(Department, null=True, backref="agents", on_delete="SET NULL")
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "agents"


class Conversation(BaseModel):
    id = AutoField()
    visitor_id = CharField(max_length=64)
    visitor_name = EncryptedCharField(max_length=512, default="Visitor")
    visitor_email = EncryptedCharField(max_length=512, default="")
    status = CharField(max_length=16, default="open")  # open | assigned | closed
    assigned_to = ForeignKeyField(Agent, null=True, backref="conversations", on_delete="SET NULL")
    site_name = CharField(max_length=128, default="")
    page_url = CharField(max_length=1024, default="")
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    closed_at = DateTimeField(null=True)
    # Güvenlik / takip meta verileri
    ip_address = CharField(max_length=64, default="")
    user_agent = CharField(max_length=512, default="")
    country = CharField(max_length=64, default="")
    city = CharField(max_length=128, default="")
    language = CharField(max_length=16, default="")
    priority = CharField(max_length=16, default="normal")  # low | normal | high
    # Departman yönlendirmesi
    department = ForeignKeyField(Department, null=True, backref="conversations", on_delete="SET NULL")

    class Meta:
        table_name = "conversations"


class Message(BaseModel):
    id = AutoField()
    conversation = ForeignKeyField(Conversation, backref="messages", on_delete="CASCADE")
    sender_type = CharField(max_length=16)  # visitor | agent | bot | system
    sender_id = CharField(max_length=64, default="")
    sender_name = CharField(max_length=128, default="")
    content = EncryptedTextField(default="")
    file_url = CharField(max_length=1024, default="")
    file_name = CharField(max_length=256, default="")
    file_size = IntegerField(default=0)
    is_read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "messages"


class CannedResponse(BaseModel):
    id = AutoField()
    title = CharField(max_length=128)
    content = TextField()
    shortcut = CharField(max_length=32, default="")
    created_by = ForeignKeyField(Agent, null=True, on_delete="SET NULL")
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "canned_responses"


class Tag(BaseModel):
    id = AutoField()
    name = CharField(max_length=64, unique=True)
    color = CharField(max_length=16, default="#6366f1")
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "tags"


class ConversationTag(BaseModel):
    conversation = ForeignKeyField(Conversation, backref="conv_tags", on_delete="CASCADE")
    tag = ForeignKeyField(Tag, backref="conv_tags", on_delete="CASCADE")
    class Meta:
        table_name = "conversation_tags"
        indexes = ((("conversation", "tag"), True),)


class BlacklistedIP(BaseModel):
    id = AutoField()
    ip = CharField(max_length=64, unique=True)  # IP adresi veya ziyaretçi ID değeri
    kind = CharField(max_length=16, default="ip")  # ip | visitor
    reason = CharField(max_length=256, default="")
    blocked_by = ForeignKeyField(Agent, null=True, on_delete="SET NULL")
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "blacklisted_ips"


class BanAppeal(BaseModel):
    id = AutoField()
    ip = CharField(max_length=64, default="")
    visitor_id = CharField(max_length=64, default="")
    message = TextField(default="")
    status = CharField(max_length=16, default="pending")  # pending | accepted | rejected
    created_at = DateTimeField(default=datetime.utcnow)
    reviewed_by = ForeignKeyField(Agent, null=True, on_delete="SET NULL")
    reviewed_at = DateTimeField(null=True)
    class Meta:
        table_name = "ban_appeals"


class Rating(BaseModel):
    id = AutoField()
    conversation = ForeignKeyField(Conversation, unique=True, backref="rating", on_delete="CASCADE")
    score = IntegerField()  # 1-5
    comment = EncryptedTextField(default="")
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "ratings"


class WorkSchedule(BaseModel):
    id = AutoField()
    agent = ForeignKeyField(Agent, unique=True, backref="schedule", on_delete="CASCADE")
    # JSON: {"mon": {"start": "09:00", "end": "18:00", "active": true}, "tue": {...}, ...}
    schedule_json = TextField(default="{}")
    timezone = CharField(max_length=64, default="Europe/Istanbul")
    class Meta:
        table_name = "work_schedules"


class BotFlow(BaseModel):
    """Deprecated — superseded by Bot/BotRule. Kept only so init_db() can
    migrate any existing row into the new schema on upgrade."""
    id = AutoField()
    name = CharField(max_length=128, default="Ana Akış")
    greeting = TextField(default="Merhaba! Size nasıl yardımcı olabilirim?")
    options_json = TextField(default="[]")
    is_active = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "bot_flows"


class Bot(BaseModel):
    id = AutoField()
    name = CharField(max_length=128, default="Bot")
    is_enabled = BooleanField(default=True)
    is_default = BooleanField(default=False)  # greets every new conversation
    greeting = TextField(default="")
    # First-contact menu, shown alongside the greeting: [{"label":"...", "reply":"...", "department_id":...}]
    options_json = TextField(default="[]")
    similarity_threshold = IntegerField(null=True)  # 0-100; null = use global Setting default
    priority = IntegerField(default=0)  # tie-break across bots when match scores are equal
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "bots"


class BotRule(BaseModel):
    id = AutoField()
    bot = ForeignKeyField(Bot, backref="rules", on_delete="CASCADE")
    triggers_json = TextField(default="[]")  # JSON list of trigger phrases
    reply = TextField(default="")
    department = ForeignKeyField(Department, null=True, on_delete="SET NULL")
    is_enabled = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "bot_rules"


class Setting(BaseModel):
    key = CharField(unique=True, max_length=64, primary_key=True)
    value = TextField(default="")
    updated_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "settings"


class Note(BaseModel):
    id = AutoField()
    conversation = ForeignKeyField(Conversation, backref="notes", on_delete="CASCADE")
    agent = ForeignKeyField(Agent, null=True, on_delete="SET NULL")
    agent_name = CharField(max_length=128, default="")
    content = EncryptedTextField()
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "notes"

class WebhookConfig(BaseModel):
    id = AutoField()
    name = CharField(max_length=64, default="Webhook")
    type = CharField(max_length=32)  # slack | discord | telegram | generic
    url = CharField(max_length=1024)
    telegram_chat_id = CharField(max_length=64, default="")
    events_json = TextField(default='["new_conversation","new_message","offline_message"]')
    is_enabled = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "webhook_configs"

class VisitorPageView(BaseModel):
    id = AutoField()
    visitor_id = CharField(max_length=64, index=True)
    url = CharField(max_length=1024, default="")
    title = CharField(max_length=256, default="")
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "visitor_page_views"

class VisitorField(BaseModel):
    id = AutoField()
    visitor_id = CharField(max_length=64)
    key = CharField(max_length=64)
    value = TextField(default="")
    class Meta:
        table_name = "visitor_fields"
        indexes = ((("visitor_id", "key"), True),)

class AuditLog(BaseModel):
    id = AutoField()
    agent_name = CharField(max_length=128, default="Sistem")
    action = CharField(max_length=64)
    target_type = CharField(max_length=32, default="")
    target_id = IntegerField(null=True)
    details = TextField(default="")
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "audit_logs"

class OfflineMessage(BaseModel):
    id = AutoField()
    visitor_id = CharField(max_length=64, default="")
    visitor_name = EncryptedCharField(max_length=512, default="")
    visitor_email = EncryptedCharField(max_length=512, default="")
    message = EncryptedTextField()
    page_url = CharField(max_length=1024, default="")
    is_read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "offline_messages"


class Form(BaseModel):
    id = AutoField()
    name = CharField(max_length=128)
    description = CharField(max_length=256, default="")
    welcome_text = CharField(max_length=512, default="Lütfen aşağıdaki formu doldurun.")
    submit_text = CharField(max_length=128, default="Gönder")
    is_active = BooleanField(default=False)
    department = ForeignKeyField(Department, null=True, backref="forms", on_delete="SET NULL")
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "forms"


class FormField(BaseModel):
    id = AutoField()
    form = ForeignKeyField(Form, backref="fields", on_delete="CASCADE")
    order = IntegerField(default=0)
    label = CharField(max_length=256)
    field_type = CharField(max_length=16, default="text")  # text|email|phone|select|textarea|rating|number
    required = BooleanField(default=True)
    placeholder = CharField(max_length=128, default="")
    # For select/radio: [{"label":"...", "reply":"..."}]
    options_json = TextField(default="[]")
    class Meta:
        table_name = "form_fields"


class FormSubmission(BaseModel):
    id = AutoField()
    form = ForeignKeyField(Form, backref="submissions", on_delete="CASCADE")
    conversation = ForeignKeyField(Conversation, null=True, backref="form_submissions", on_delete="SET NULL")
    visitor_id = CharField(max_length=64, default="")
    answers_json = TextField(default="{}")  # {field_id_str: answer_str}
    submitted_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "form_submissions"


class DeletedVisitorArchive(BaseModel):
    """Soft-delete bin: when an admin wipes a visitor's data we snapshot it
    here as JSON for a short recovery window (see ARCHIVE_RETENTION_DAYS) so an
    accidental deletion can be restored, then it's purged for good."""
    id = AutoField()
    visitor_id = CharField(max_length=64, index=True)
    payload_json = EncryptedTextField(default="{}")  # full snapshot of the wiped rows
    item_count = IntegerField(default=0)              # how many rows were archived (for the UI)
    deleted_by = CharField(max_length=128, default="")
    deleted_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "deleted_visitor_archives"


ARCHIVE_RETENTION_DAYS = 14


class CookieCategory(BaseModel):
    """A consent group (e.g. Necessary, Analytics, Marketing). Visitors can
    accept/reject optional categories; required ones are always on."""
    id = AutoField()
    key = CharField(unique=True, max_length=64)
    name = CharField(max_length=128)
    description = TextField(default="")
    is_required = BooleanField(default=False)
    order = IntegerField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "cookie_categories"


class CookieDefinition(BaseModel):
    """A single cookie/storage item the admin documents for the visitor-facing
    cookie notice (e.g. "session_id" — mandatory, "analytics" — optional)."""
    id = AutoField()
    name = CharField(max_length=128)
    description = TextField(default="")
    is_mandatory = BooleanField(default=False)
    category_key = CharField(max_length=64, default="necessary")
    provider = CharField(max_length=128, default="")
    duration = CharField(max_length=64, default="")
    order = IntegerField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "cookie_definitions"


class CookieConsentLog(BaseModel):
    """Record of a visitor's cookie consent choices, kept for compliance."""
    id = AutoField()
    visitor_id = CharField(max_length=64, index=True)
    choices_json = EncryptedTextField(default="{}")
    accepted_categories = CharField(max_length=512, default="")
    ip_address = CharField(max_length=64, default="")
    user_agent = CharField(max_length=512, default="")
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "cookie_consent_logs"


_DEFAULT_COOKIE_CATEGORIES = [
    {"key": "necessary",  "name": "Necessary",  "description": "Required for the chat to work. Always on.", "is_required": True,  "order": 0},
    {"key": "functional", "name": "Functional", "description": "Remembers your preferences (language, name).",  "is_required": False, "order": 1},
    {"key": "analytics",  "name": "Analytics",  "description": "Anonymous usage statistics.",                   "is_required": False, "order": 2},
    {"key": "marketing",  "name": "Marketing",  "description": "Advertising and retargeting.",                  "is_required": False, "order": 3},
]


def _seed_cookie_categories():
    """Seed a sensible default category set the first time, so consent mode
    works out of the box. Never touches categories the admin already made."""
    if CookieCategory.select().count() > 0:
        return
    for c in _DEFAULT_COOKIE_CATEGORIES:
        CookieCategory.create(**c)


def _migrate_botflow_to_bot():
    """One-time, best-effort copy of the old single BotFlow row into the new
    Bot model as the default bot. Never overwrites bots a user already made."""
    if Bot.select().count() > 0:
        return
    try:
        old = BotFlow.get_or_none(BotFlow.is_active == True) or BotFlow.select().order_by(BotFlow.created_at).first()
    except Exception:
        old = None
    if old:
        Bot.create(
            name=old.name, is_enabled=True, is_default=True,
            greeting=old.greeting, options_json=old.options_json,
        )


def init_db():
    with database:
        database.create_tables([
            Department, Agent, Conversation, Message, CannedResponse,
            Tag, ConversationTag, BlacklistedIP, BanAppeal, Rating, WorkSchedule, Setting,
            Bot, BotRule,
            Note, WebhookConfig, VisitorPageView, VisitorField, AuditLog, OfflineMessage,
            Form, FormField, FormSubmission, DeletedVisitorArchive,
            CookieDefinition, CookieCategory, CookieConsentLog,
        ], safe=True)
        _migrate_botflow_to_bot()
        _safe_migrations = [
            "ALTER TABLE agents ADD COLUMN avatar_color VARCHAR(20) DEFAULT '#6366f1'",
            "ALTER TABLE agents ADD COLUMN department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL",
            "ALTER TABLE conversations ADD COLUMN ip_address VARCHAR(64) DEFAULT ''",
            "ALTER TABLE conversations ADD COLUMN user_agent VARCHAR(512) DEFAULT ''",
            "ALTER TABLE conversations ADD COLUMN country VARCHAR(64) DEFAULT ''",
            "ALTER TABLE conversations ADD COLUMN city VARCHAR(128) DEFAULT ''",
            "ALTER TABLE conversations ADD COLUMN language VARCHAR(16) DEFAULT ''",
            "ALTER TABLE conversations ADD COLUMN priority VARCHAR(16) DEFAULT 'normal'",
            "ALTER TABLE conversations ADD COLUMN department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL",
            "ALTER TABLE blacklisted_ips ADD COLUMN kind VARCHAR(16) DEFAULT 'ip'",
            "ALTER TABLE agents ADD COLUMN permissions TEXT DEFAULT '[]'",
            "ALTER TABLE cookie_definitions ADD COLUMN category_key VARCHAR(64) DEFAULT 'necessary'",
            "ALTER TABLE cookie_definitions ADD COLUMN provider VARCHAR(128) DEFAULT ''",
            "ALTER TABLE cookie_definitions ADD COLUMN duration VARCHAR(64) DEFAULT ''",
        ]
        for _sql in _safe_migrations:
            try:
                database.execute_sql(_sql)
            except Exception:
                pass
        _seed_cookie_categories()
