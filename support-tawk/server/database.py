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

db_cfg = config.database

def _make_db():
    t = db_cfg.type.lower()
    if t == "sqlite":
        Path(db_cfg.path).parent.mkdir(parents=True, exist_ok=True)
        return SqliteDatabase(db_cfg.path, pragmas={"journal_mode": "wal", "foreign_keys": 1})
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
    role = CharField(max_length=16, default="agent")  # admin | agent | supervisor
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
    visitor_name = CharField(max_length=128, default="Ziyaretçi")
    visitor_email = CharField(max_length=256, default="")
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
    content = TextField(default="")
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


class Rating(BaseModel):
    id = AutoField()
    conversation = ForeignKeyField(Conversation, unique=True, backref="rating", on_delete="CASCADE")
    score = IntegerField()  # 1-5
    comment = TextField(default="")
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
    id = AutoField()
    name = CharField(max_length=128, default="Ana Akış")
    greeting = TextField(default="Merhaba! Size nasıl yardımcı olabilirim?")
    # JSON: [{"label": "Teknik Destek", "reply": "Teknik destek ekibine bağlanıyorum..."}, ...]
    options_json = TextField(default="[]")
    is_active = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "bot_flows"


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
    content = TextField()
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
    visitor_name = CharField(max_length=128, default="")
    visitor_email = CharField(max_length=256, default="")
    message = TextField()
    page_url = CharField(max_length=1024, default="")
    is_read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    class Meta:
        table_name = "offline_messages"


def init_db():
    with database:
        database.create_tables([
            Department, Agent, Conversation, Message, CannedResponse,
            Tag, ConversationTag, BlacklistedIP, Rating, WorkSchedule, BotFlow, Setting,
            Note, WebhookConfig, VisitorPageView, VisitorField, AuditLog, OfflineMessage
        ], safe=True)
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
        ]
        for _sql in _safe_migrations:
            try:
                database.execute_sql(_sql)
            except Exception:
                pass
