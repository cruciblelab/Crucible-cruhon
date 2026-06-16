from __future__ import annotations
import os
import uuid
import mimetypes
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from ..config import config
from ..auth import get_current_agent
from ..database import Message, Conversation
from ..ws_manager import manager
from datetime import datetime

router = APIRouter(prefix="/api/files")

# Absolute path so it never depends on CWD
UPLOAD_DIR = (Path(__file__).parent.parent.parent / "uploads").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

_IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "webp"}
# All allowed extensions (union of image + file lists from config is checked at
# upload time; at serve time we re-derive from config to stay in sync)
_SAFE_FILENAME_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
)


def _ext(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _size_limit(ext: str) -> int:
    if ext in _IMAGE_EXTS:
        return config.limits.max_image_size_mb * 1024 * 1024
    return config.limits.max_file_size_mb * 1024 * 1024


def _safe_serve_path(filename: str) -> Path:
    """Resolve filename to an absolute path that must be inside UPLOAD_DIR.
    Raises HTTPException 400 on obviously bad input, 403 on traversal attempt."""
    # Reject any filename that contains separators or non-safe chars upfront
    # (uploaded files are always uuid4.ext so this also rejects legacy junk)
    if not filename or "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Invalid filename")
    if not all(c in _SAFE_FILENAME_CHARS for c in filename):
        raise HTTPException(400, "Invalid filename")
    resolved = (UPLOAD_DIR / filename).resolve()
    # Must be strictly inside UPLOAD_DIR (trailing sep prevents prefix collision)
    if not str(resolved).startswith(str(UPLOAD_DIR) + os.sep):
        raise HTTPException(403, "Access denied")
    return resolved


@router.post("/upload/visitor/{visitor_id}")
async def visitor_upload(visitor_id: str, file: UploadFile = File(...)):
    ext = _ext(file.filename or "")
    if ext not in config.limits.allowed_file_types:
        raise HTTPException(400, f"İzin verilmeyen dosya türü: {ext}")

    content = await file.read()
    size_limit = _size_limit(ext)
    if len(content) > size_limit:
        mb = size_limit // (1024 * 1024)
        raise HTTPException(400, f"Dosya boyutu {mb}MB'ı geçemez")

    safe_name = f"{uuid.uuid4().hex}.{ext}"
    dest = UPLOAD_DIR / safe_name
    dest.write_bytes(content)

    url = f"/api/files/serve/{safe_name}"

    conv = Conversation.get_or_none(
        Conversation.visitor_id == visitor_id,
        Conversation.status != "closed"
    )
    if conv:
        msg = Message.create(
            conversation=conv,
            sender_type="visitor",
            sender_id=visitor_id,
            sender_name=conv.visitor_name,
            content="",
            file_url=url,
            file_name=file.filename,
            file_size=len(content),
        )
        Conversation.update(updated_at=datetime.utcnow()).where(Conversation.id == conv.id).execute()
        payload = {
            "type": "message",
            "conversation_id": conv.id,
            "message": {
                "id": msg.id,
                "sender_type": "visitor",
                "sender_name": conv.visitor_name,
                "content": "",
                "file_url": url,
                "file_name": file.filename,
                "created_at": msg.created_at.isoformat(),
            }
        }
        await manager.broadcast_to_watchers(conv.id, payload)
        await manager.broadcast_to_agents(payload)

    return {"url": url, "filename": file.filename, "size": len(content)}


@router.post("/upload/agent/{conversation_id}")
async def agent_upload(
    conversation_id: int,
    file: UploadFile = File(...),
    agent=Depends(get_current_agent)
):
    ext = _ext(file.filename or "")
    if ext not in config.limits.allowed_file_types:
        raise HTTPException(400, f"İzin verilmeyen dosya türü: {ext}")

    content = await file.read()
    size_limit = _size_limit(ext)
    if len(content) > size_limit:
        mb = size_limit // (1024 * 1024)
        raise HTTPException(400, f"Dosya boyutu {mb}MB'ı geçemez")

    safe_name = f"{uuid.uuid4().hex}.{ext}"
    dest = UPLOAD_DIR / safe_name
    dest.write_bytes(content)

    url = f"/api/files/serve/{safe_name}"

    conv = Conversation.get_or_none(Conversation.id == conversation_id)
    if conv:
        msg = Message.create(
            conversation=conv,
            sender_type="agent",
            sender_id=str(agent.id),
            sender_name=agent.display_name or agent.username,
            content="",
            file_url=url,
            file_name=file.filename,
            file_size=len(content),
        )
        Conversation.update(updated_at=datetime.utcnow()).where(Conversation.id == conv.id).execute()
        payload = {
            "type": "message",
            "conversation_id": conv.id,
            "message": {
                "id": msg.id,
                "sender_type": "agent",
                "sender_name": agent.display_name or agent.username,
                "content": "",
                "file_url": url,
                "file_name": file.filename,
                "created_at": msg.created_at.isoformat(),
            }
        }
        await manager.send_to_visitor(conv.visitor_id, payload)
        await manager.broadcast_to_watchers(conv.id, payload)

    return {"url": url, "filename": file.filename, "size": len(content)}


@router.get("/serve/{filename}")
def serve_file(filename: str):
    path = _safe_serve_path(filename)
    ext = _ext(filename)
    allowed = set(config.limits.allowed_file_types) | _IMAGE_EXTS
    if ext not in allowed:
        raise HTTPException(403, "Access denied")
    if not path.is_file():
        raise HTTPException(404, "File not found")
    mime, _ = mimetypes.guess_type(str(path))
    return FileResponse(
        str(path),
        media_type=mime or "application/octet-stream",
        filename=filename,
    )
