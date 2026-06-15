from __future__ import annotations
import httpx
from .config import config


async def handle_ai_reply(conv, user_message: str) -> str | None:
    if not config.ai.enabled or not config.ai.api_key:
        return None

    from .database import Message
    recent = list(
        Message.select()
        .where(Message.conversation == conv)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    recent.reverse()

    messages = [{"role": "system", "content": config.ai.system_prompt}]
    for m in recent:
        if m.sender_type == "visitor":
            messages.append({"role": "user", "content": m.content})
        elif m.sender_type in ("agent", "bot"):
            messages.append({"role": "assistant", "content": m.content})

    provider = config.ai.provider.lower()

    try:
        if provider == "openai":
            return await _openai_reply(messages)
        elif provider == "anthropic":
            return await _anthropic_reply(messages, user_message)
    except Exception as e:
        print(f"[AI] Hata: {e}")
    return None


async def _openai_reply(messages: list) -> str | None:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {config.ai.api_key}"},
            json={"model": config.ai.model, "messages": messages, "max_tokens": 500},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


async def _anthropic_reply(messages: list, last_user: str) -> str | None:
    # Convert to Anthropic format (system separate)
    system = ""
    anthro_msgs = []
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
        else:
            anthro_msgs.append({"role": m["role"], "content": m["content"]})

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": config.ai.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": config.ai.model,
                "max_tokens": 500,
                "system": system,
                "messages": anthro_msgs,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"].strip()
