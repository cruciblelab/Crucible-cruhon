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
    language: str = "en"


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
    welcome_message: str = "Hello! How can I help you?"
    offline_message: str = "We're offline right now. Leave a message and we'll get back to you."
    response_time_text: str = "Usually replies within a few minutes"
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
    system_prompt: str = "You are a customer support assistant. Be polite and helpful."
    auto_reply: bool = True
    handoff_message: str = "Connecting you to a support agent, please wait."
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


def _load_dotenv(path: str = ".env") -> None:
    """Minimal .env loader: KEY=VALUE lines into os.environ (no overwrite).
    Keeps secrets out of config.yml / version control."""
    env_file = Path(os.environ.get("SUPPORT_TAWK_ENV", path))
    if not env_file.exists():
        return
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except Exception:
        pass


def _apply_env_overrides(cfg: AppConfig) -> None:
    """Secrets and a few operational values may come from the environment.
    Environment always wins over config.yml so secrets never live in YAML."""
    env = os.environ
    if env.get("SECRET_KEY"):
        cfg.server.secret_key = env["SECRET_KEY"]
    if env.get("ADMIN_PASSWORD"):
        cfg.admin.default_password = env["ADMIN_PASSWORD"]
    if env.get("AI_API_KEY"):
        cfg.ai.api_key = env["AI_API_KEY"]
    if env.get("SUPPORT_TAWK_PORT"):
        try:
            cfg.server.port = int(env["SUPPORT_TAWK_PORT"])
        except ValueError:
            pass


def load_config(path: str = _CONFIG_PATH) -> AppConfig:
    _load_dotenv()
    cfg = AppConfig()
    config_file = Path(path)
    if config_file.exists():
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
    _apply_env_overrides(cfg)
    return cfg


config: AppConfig = load_config()
