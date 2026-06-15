from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

# Allow running from the support-tawk directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from server.config import config
from server.database import database, Agent, Conversation, Message, init_db
from server.auth import hash_password
from server.routes.chat import router as chat_router
from server.routes.admin import router as admin_router
from server.routes.files import router as files_router


async def _cleanup_loop():
    while True:
        await asyncio.sleep(86400)  # günde bir
        try:
            cutoff = datetime.utcnow() - timedelta(days=7)
            old_ids = [c.id for c in Conversation.select(Conversation.id)
                       .where(Conversation.status == "closed", Conversation.closed_at < cutoff)]
            if old_ids:
                Message.delete().where(Message.conversation_id.in_(old_ids)).execute()
                Conversation.delete().where(Conversation.id.in_(old_ids)).execute()
                print(f"[Support Tawk] {len(old_ids)} eski konuşma silindi")
        except Exception as e:
            print(f"[Support Tawk] Temizlik hatası: {e}")


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
            display_name="Yönetici",
            role="admin",
        )
        print(f"[Support Tawk] Admin hesabı oluşturuldu: {config.admin.default_username}")


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

app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(files_router)

# Serve static files (widget + admin panel)
_static = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static)), name="static")


@app.get("/widget.js")
def serve_widget():
    return FileResponse(str(_static / "widget.js"), media_type="application/javascript")


@app.get("/admin", include_in_schema=False)
@app.get("/admin/{path:path}", include_in_schema=False)
def serve_admin(path: str = ""):
    return FileResponse(str(_static / "admin" / "index.html"))


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


@app.get("/api/config")
def public_config():
    return {
        "site_name": config.site.name,
        "widget_color": config.chat.widget_color,
        "welcome_message": config.chat.welcome_message,
        "offline_message": config.chat.offline_message,
        "response_time_text": config.chat.response_time_text,
        "notification_sound": config.chat.notification_sound,
        "logo_url": config.site.logo_url,
        "proactive_delay_seconds": getattr(config.chat, "proactive_delay_seconds", 0),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,
    )
