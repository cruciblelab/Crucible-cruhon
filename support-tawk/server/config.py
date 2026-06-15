from __future__ import annotations
import yaml
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

_CONFIG_PATH = os.environ.get("SUPPORT_TAWK_CONFIG", "config.yml")


@dataclass
class SiteConfig:
    name: str = "Support Tawk"
    domain: str = ""
    logo_url: str = ""


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "changeme"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class AdminConfig:
    default_username: str = "admin"
    default_password: str = "admin123"
    session_hours: int = 24


@dataclass
class DatabaseConfig:
    type: str = "sqlite"
    path: str = "./data/support.db"
    host: str = "localhost"
    port: int = 5432
    name: str = "support_tawk"
    username: str = ""
    password: str = ""


@dataclass
class ChatConfig:
    widget_color: str = "#2563eb"
    welcome_message: str = "Merhaba! Size nasıl yardımcı olabilirim?"
    offline_message: str = "Şu an çevrimdışıyız, mesajınızı bırakın."
    response_time_text: str = "Genellikle birkaç dakika içinde yanıtlarız"
    notification_sound: bool = True


@dataclass
class LimitsConfig:
    max_file_size_mb: int = 10
    max_image_size_mb: int = 5
    allowed_file_types: List[str] = field(
        default_factory=lambda: ["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx", "txt", "zip"]
    )
    max_message_length: int = 4000
    conversations_per_page: int = 20


@dataclass
class AIConfig:
    enabled: bool = False
    provider: str = "openai"
    api_key: str = ""
    model: str = "gpt-3.5-turbo"
    system_prompt: str = "Sen bir müşteri destek asistanısın. Kibarca ve yardımcı ol."
    auto_reply: bool = True
    handoff_message: str = "Sizi bir destek temsilcisine bağlıyorum, lütfen bekleyin."
    confidence_threshold: float = 0.7


@dataclass
class AppConfig:
    site: SiteConfig = field(default_factory=SiteConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    admin: AdminConfig = field(default_factory=AdminConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    chat: ChatConfig = field(default_factory=ChatConfig)
    limits: LimitsConfig = field(default_factory=LimitsConfig)
    ai: AIConfig = field(default_factory=AIConfig)


def _apply(dataclass_obj, data: dict):
    for key, val in data.items():
        if hasattr(dataclass_obj, key):
            setattr(dataclass_obj, key, val)


def load_config(path: str = _CONFIG_PATH) -> AppConfig:
    cfg = AppConfig()
    config_file = Path(path)
    if not config_file.exists():
        return cfg
    with open(config_file, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if "site" in raw:
        _apply(cfg.site, raw["site"])
    if "server" in raw:
        _apply(cfg.server, raw["server"])
    if "admin" in raw:
        _apply(cfg.admin, raw["admin"])
    if "database" in raw:
        _apply(cfg.database, raw["database"])
    if "chat" in raw:
        _apply(cfg.chat, raw["chat"])
    if "limits" in raw:
        _apply(cfg.limits, raw["limits"])
    if "ai" in raw:
        _apply(cfg.ai, raw["ai"])
    return cfg


config: AppConfig = load_config()
