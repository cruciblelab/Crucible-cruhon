from __future__ import annotations
import re
import httpx
from .config import config

# Matches a leading "CONFIDENCE: 0.83" style marker (see _confidence_instruction).
_CONF_NUM_RE = re.compile(r"([01](?:\.\d+)?|0?\.\d+)")


def _confidence_instruction() -> str:
    return (
        "\n\nBefore your reply, output a single line in the exact form "
        "'CONFIDENCE: X', where X is a number between 0 and 1 indicating how "
        "confident you are that you can answer correctly and completely. "
        "Then write your reply on the following lines."
    )


def _split_confidence(text: str):
    """Pull a leading 'CONFIDENCE: X' marker off an AI reply.

    Returns (confidence_or_None, cleaned_reply). The marker line is always
    stripped when present; an unparseable number yields a None confidence
    (treated as "confident" so we never block a reply over a format glitch).
    """
    if not text:
        return None, text
    lines = text.split("\n")
    if lines and lines[0].strip().lower().startswith("confidence"):
        m = _CONF_NUM_RE.search(lines[0])
        conf = float(m.group(1)) if m else None
        return conf, "\n".join(lines[1:]).strip()
    return None, text


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

    use_confidence = config.ai.confidence_threshold and config.ai.confidence_threshold > 0
    system_prompt = config.ai.system_prompt
    if use_confidence:
        system_prompt += _confidence_instruction()

    messages = [{"role": "system", "content": system_prompt}]
    for m in recent:
        if m.sender_type == "visitor":
            messages.append({"role": "user", "content": m.content})
        elif m.sender_type in ("agent", "bot"):
            messages.append({"role": "assistant", "content": m.content})

    provider = config.ai.provider.lower()

    raw = None
    try:
        if provider == "openai":
            raw = await _openai_reply(messages)
        elif provider == "anthropic":
            raw = await _anthropic_reply(messages)
    except Exception as e:
        print(f"[AI] Hata: {e}")
        return None

    if not raw:
        return None

    if use_confidence:
        confidence, reply = _split_confidence(raw)
        if confidence is not None and confidence < config.ai.confidence_threshold:
            # Not sure enough to answer on its own — defer to a human.
            return config.ai.handoff_message or None
        return reply or None

    return raw


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


async def _anthropic_reply(messages: list) -> str | None:
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
