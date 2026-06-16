from __future__ import annotations
import asyncio
import json
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from server.config import config
from server.database import database, Agent, Conversation, Message, Setting, init_db
from server.auth import hash_password
from server.ws_manager import manager
from server.routes.chat import router as chat_router
from server.routes.admin import router as admin_router
from server.routes.files import router as files_router
from server.routes.forms import router as forms_router

_static = Path(__file__).parent / "static"
_SUPPORTED_LANGS = {"en", "tr"}


async def _cleanup_loop():
    while True:
        await asyncio.sleep(86400)
        try:
            cutoff = datetime.utcnow() - timedelta(days=14)
            old_ids = [c.id for c in Conversation.select(Conversation.id)
                       .where(Conversation.status == "closed", Conversation.closed_at < cutoff)]
            if old_ids:
                Message.delete().where(Message.conversation_id.in_(old_ids)).execute()
                Conversation.delete().where(Conversation.id.in_(old_ids)).execute()
                print(f"[Support Tawk] Deleted {len(old_ids)} old conversations")
        except Exception as e:
            print(f"[Support Tawk] Cleanup error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _seed_admin()
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()


def _seed_admin():
    if not Agent.get_or_none(Agent.username == config.admin.default_username):
        Agent.create(
            username=config.admin.default_username,
            password_hash=hash_password(config.admin.default_password),
            display_name="Administrator",
            role="admin",
        )
        print(f"[Support Tawk] Admin account created: {config.admin.default_username}")


app = FastAPI(
    title="Support Tawk",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compress JSON/HTML/JS responses — cuts bandwidth on conversation lists,
# locale files and the admin bundle by roughly 60-70%.
app.add_middleware(GZipMiddleware, minimum_size=600)


# Security headers added to every response. The admin panel relies on inline
# scripts/styles, so we apply transport/sniffing protections rather than a
# strict CSP that would break it.
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-XSS-Protection": "1; mode=block",
}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for k, v in _SECURITY_HEADERS.items():
        response.headers.setdefault(k, v)
    return response

app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(files_router)
app.include_router(forms_router)

app.mount("/static", StaticFiles(directory=str(_static)), name="static")


@app.get("/widget.js")
def serve_widget():
    return FileResponse(str(_static / "widget.js"), media_type="application/javascript")


@app.get("/admin", include_in_schema=False)
@app.get("/admin/{path:path}", include_in_schema=False)
def serve_admin(path: str = ""):
    if path:
        admin_dir = (_static / "admin").resolve()
        candidate = (admin_dir / path).resolve()
        if str(candidate).startswith(str(admin_dir) + os.sep) and candidate.is_file():
            return FileResponse(str(candidate))
    return FileResponse(str(_static / "admin" / "index.html"))


@app.get("/api/locale/{lang}")
def get_locale(lang: str):
    lang = lang.lower()
    if lang not in _SUPPORTED_LANGS:
        lang = "en"
    locale_file = _static / "locales" / f"{lang}.json"
    if not locale_file.exists():
        raise HTTPException(status_code=404, detail="Locale not found")
    with open(locale_file, encoding="utf-8") as f:
        return JSONResponse(json.load(f))


@app.get("/")
def root():
    return {
        "name": "Support Tawk",
        "version": "1.0.0",
        "site": config.site.name,
        "admin_panel": "/admin",
        "widget": "/widget.js",
        "docs": "/api/docs",
    }


@app.get("/health", include_in_schema=False)
def health():
    """Lightweight liveness/readiness probe for monitoring and uptime tools.
    Returns 200 when the database is reachable, 503 otherwise."""
    db_ok = True
    try:
        database.execute_sql("SELECT 1")
    except Exception:
        db_ok = False
    payload = {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "agents_online": manager.agent_count(),
    }
    return JSONResponse(payload, status_code=200 if db_ok else 503)


@app.get("/api/config")
def public_config():
    from server.settings_cache import get_settings
    overrides = get_settings()
    try:
        bubbles = json.loads(overrides.get("proactive_bubbles", "[]"))
        if not isinstance(bubbles, list):
            bubbles = []
    except Exception:
        bubbles = []
    try:
        widget_width = int(overrides.get("widget_width", "360") or 360)
    except Exception:
        widget_width = 360
    try:
        widget_radius = int(overrides.get("widget_radius", "16") or 16)
    except Exception:
        widget_radius = 16
    try:
        bubble_dismiss_days = int(overrides.get("bubble_dismiss_days", "0") or 0)
    except Exception:
        bubble_dismiss_days = 0
    try:
        widget_texts = json.loads(overrides.get("widget_texts", "{}"))
        if not isinstance(widget_texts, dict):
            widget_texts = {}
    except Exception:
        widget_texts = {}

    active_lang = overrides.get("language", config.site.language) or "en"
    # Legacy key migration
    if active_lang == "en" and overrides.get("widget_lang") == "tr":
        active_lang = "tr"
    if active_lang not in _SUPPORTED_LANGS:
        active_lang = "en"

    return {
        "site_name": overrides.get("site_name", config.site.name),
        "widget_color": overrides.get("widget_color", config.chat.widget_color),
        "welcome_message": overrides.get("welcome_message", config.chat.welcome_message),
        "offline_message": overrides.get("offline_message", config.chat.offline_message),
        "response_time_text": config.chat.response_time_text,
        "notification_sound": overrides.get("notification_sound", "true") != "false",
        "logo_url": config.site.logo_url,
        "proactive_delay_seconds": int(overrides.get("proactive_delay_seconds", "0")),
        "widget_width": widget_width,
        "proactive_bubbles": bubbles,
        "widget_position": overrides.get("widget_position", "right"),
        "language": active_lang,
        "widget_icon": overrides.get("widget_icon", ""),
        "widget_radius": widget_radius,
        "widget_texts": widget_texts,
        "bubble_dismiss_days": bubble_dismiss_days,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,
    )
