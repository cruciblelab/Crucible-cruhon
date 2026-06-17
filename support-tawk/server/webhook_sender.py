from __future__ import annotations
import asyncio
import json
import httpx
from .database import WebhookConfig


async def fire_event(event_type: str, data: dict):
    hooks = list(WebhookConfig.select().where(WebhookConfig.is_enabled == True))
    for hook in hooks:
        try:
            events = json.loads(hook.events_json or "[]")
        except Exception:
            events = []
        if event_type not in events and event_type != "test":
            continue
        asyncio.create_task(_dispatch(hook, event_type, data))


async def _dispatch(hook, event_type: str, data: dict):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if hook.type == "telegram":
                text = _fmt_telegram(event_type, data)
                chat_id = hook.telegram_chat_id
                if not chat_id:
                    return
                await client.post(hook.url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
            elif hook.type == "discord":
                await client.post(hook.url, json={"content": _fmt_discord(event_type, data)})
            elif hook.type == "slack":
                await client.post(hook.url, json={"text": _fmt_slack(event_type, data)})
            else:
                await client.post(hook.url, json={"event": event_type, "data": data, "timestamp": _now()})
    except Exception as e:
        print(f"[Webhook] {hook.type} dispatch error: {e}")


def _now():
    from datetime import datetime
    return datetime.utcnow().isoformat()


def _conv_text(data):
    c = data.get("conversation", {})
    return f"#{c.get('id','?')} – {c.get('visitor_name','Ziyaretçi')} ({c.get('page_url','')})"


def _fmt_slack(event_type: str, data: dict) -> str:
    if event_type == "new_conversation":
        return f"💬 *Yeni konuşma*: {_conv_text(data)}"
    if event_type == "new_message":
        msg = data.get("message", {})
        return f"📩 *Yeni mesaj* (#{data.get('conversation_id','?')}): {msg.get('content','')[:300]}"
    if event_type == "offline_message":
        return f"📬 *Çevrimdışı mesaj*: {data.get('visitor_name','')} <{data.get('visitor_email','')}>\n{data.get('message','')[:300]}"
    return f"[{event_type}] {json.dumps(data)[:400]}"


def _fmt_discord(event_type: str, data: dict) -> str:
    if event_type == "new_conversation":
        return f"💬 **Yeni konuşma**: {_conv_text(data)}"
    if event_type == "new_message":
        msg = data.get("message", {})
        return f"📩 **Yeni mesaj** (#{data.get('conversation_id','?')}): {msg.get('content','')[:300]}"
    if event_type == "offline_message":
        return f"📬 **Çevrimdışı mesaj**: {data.get('visitor_name','')} <{data.get('visitor_email','')}>\n{data.get('message','')[:300]}"
    return f"[{event_type}] {json.dumps(data)[:400]}"


def _fmt_telegram(event_type: str, data: dict) -> str:
    if event_type == "new_conversation":
        c = data.get("conversation", {})
        return f"💬 <b>Yeni konuşma</b>\n#{c.get('id','?')} – {c.get('visitor_name','Ziyaretçi')}\n{c.get('page_url','')}"
    if event_type == "new_message":
        msg = data.get("message", {})
        content = (msg.get('content','') or '')[:300]
        return f"📩 <b>Yeni mesaj</b> (#{data.get('conversation_id','?')})\n{content}"
    if event_type == "offline_message":
        return (f"📬 <b>Çevrimdışı mesaj</b>\n"
                f"{data.get('visitor_name','')} &lt;{data.get('visitor_email','')}&gt;\n"
                f"{data.get('message','')[:300]}")
    return f"[{event_type}]\n{json.dumps(data)[:400]}"
