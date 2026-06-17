"""
Tiny in-process cache + matching engine for the multi-bot keyword system.

Mirrors the settings_cache.py pattern: a short-TTL cache of the enabled
bots/rules (read on every visitor message otherwise), explicitly invalidated
whenever an admin writes to /api/admin/bots*.

Fuzzy matching uses rapidfuzz's partial_ratio, which scores how well the
trigger phrase matches *some substring* of the visitor's message - this is
what we want, since a short trigger ("iade", "kargo ne zaman") is usually
embedded in a longer free-form sentence rather than equal to it.
"""
from __future__ import annotations
import json
import time
import threading
from rapidfuzz import fuzz

_TTL = 30.0  # seconds
_lock = threading.Lock()
_cache: list[dict] | None = None
_expires_at: float = 0.0

DEFAULT_THRESHOLD = 70


def _global_default_threshold() -> int:
    from .settings_cache import get_settings
    raw = get_settings().get("bot_default_threshold")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return DEFAULT_THRESHOLD


def _load_enabled_bots() -> list[dict]:
    global _cache, _expires_at
    now = time.monotonic()
    with _lock:
        if _cache is not None and now < _expires_at:
            return _cache

    # Import here to avoid a circular import at module load time.
    from .database import Bot, BotRule
    default_threshold = _global_default_threshold()

    bots = []
    for bot in Bot.select().where(Bot.is_enabled == True):
        threshold = bot.similarity_threshold
        if threshold is None:
            threshold = default_threshold
        rules = []
        for rule in (BotRule.select()
                     .where((BotRule.bot_id == bot.id) & (BotRule.is_enabled == True))):
            try:
                triggers = [t.strip() for t in json.loads(rule.triggers_json or "[]") if t and t.strip()]
            except Exception:
                triggers = []
            if not triggers:
                continue
            rules.append({
                "id": rule.id,
                "triggers": triggers,
                "reply": rule.reply,
                "department_id": rule.department_id,
            })
        if not rules:
            continue
        bots.append({
            "id": bot.id,
            "name": bot.name,
            "priority": bot.priority,
            "threshold": threshold,
            "rules": rules,
        })

    with _lock:
        _cache = bots
        _expires_at = time.monotonic() + _TTL
    return bots


def invalidate() -> None:
    """Drop the cache immediately (call after writing bots/rules/settings)."""
    global _cache, _expires_at
    with _lock:
        _cache = None
        _expires_at = 0.0


def find_best_match(message: str) -> dict | None:
    """Return the best-scoring rule across all enabled bots whose score
    clears that bot's similarity threshold, or None if nothing matched.

    Ties on score are broken by bot priority (higher wins).
    """
    text = (message or "").strip()
    if not text:
        return None

    best: dict | None = None
    for bot in _load_enabled_bots():
        for rule in bot["rules"]:
            score = max(fuzz.partial_ratio(trigger.lower(), text.lower()) for trigger in rule["triggers"])
            if score < bot["threshold"]:
                continue
            if best is None or score > best["score"] or (score == best["score"] and bot["priority"] > best["bot_priority"]):
                best = {
                    "bot_id": bot["id"],
                    "bot_name": bot["name"],
                    "bot_priority": bot["priority"],
                    "rule_id": rule["id"],
                    "reply": rule["reply"],
                    "department_id": rule["department_id"],
                    "score": score,
                }
    return best
