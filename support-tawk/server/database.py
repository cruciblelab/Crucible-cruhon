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


class Agent(BaseModel):
    id = AutoField()
    username = CharField(unique=True, max_length=64)
    password_hash = CharField(max_length=256)
    display_name = CharField(max_length=128, default="")
    role = CharField(max_length=16, default="agent")  # admin | agent
    is_active = BooleanField(default=True)
    is_online = BooleanField(default=False)
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
    ip = CharField(max_length=64, unique=True)
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


def init_db():
    with database:
        database.create_tables([
            Agent, Conversation, Message, CannedResponse,
            Tag, ConversationTag, BlacklistedIP, Rating, WorkSchedule, BotFlow
        ], safe=True)
