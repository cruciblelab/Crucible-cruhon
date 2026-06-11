# cruhon-discord — Full Python Freedom Design

> Goal: 100% of discord.py accessible from Cruhon.
> Every Python operation possible with discord.py should be possible with Cruhon.
> discord.py 2.7.1 — 253 classes · 66 sub-modules · ~5000 methods/properties

---

## 1. Philosophy — Why "5000 wrappers" is the wrong approach

The lesson learned from stdlib: **passthrough instead of wrapping every module**.
Same applies to discord.py. Three layers:

```
┌─────────────────────────────────────────────────────────┐
│ LAYER 2 — Block commands (complex scaffolding)          │
│ @discord.view / button / select / modal / cog / group   │
├─────────────────────────────────────────────────────────┤
│ LAYER 1 — Ergonomic shortcuts (~60 → ~90 commands)      │
│ @discord.send / ban / embed / thread / webhook / poll    │
├─────────────────────────────────────────────────────────┤
│ LAYER 0 — Universal passthrough (FULL FREEDOM)          │
│ @discord.X[...]  ·  @discord.ui.Y[...]  ·  raw Python   │
└─────────────────────────────────────────────────────────┘
```

The more powerful the lower layer, the more optional the upper layers become
(ergonomic shortcuts, not requirements).

---

## 2. Current state — what works / what doesn't

| Capability | Status | Mechanism |
|---|---|---|
| `@discord.Embed["t"; "d"]` → `discord.Embed("t","d")` | ✅ | LibCallNode fallback |
| `@discord.Color.blue[]` | ✅ | lexer_hook nested rewrite |
| `@discord.ui.Button[...]` | ✅ | lexer_hook nested rewrite |
| `message.author`, `guild.members` | ✅ | `@var[x; message.author]` raw Python |
| `await msg.add_reaction("👍")` | ✅ | `@var`/`@raw` raw Python |
| View/Button/Modal class | ✅ | `@discord.view` / `@discord.button` block commands |
| Cog class | ✅ | `@discord.cog` block command |
| `@discord.utils.get[...]` | ✅ | lexer_hook nested rewrite |

---

## 3. LAYER 0 — Universal Passthrough (Core)

> **⚠️ CRITICAL PRINCIPLE: ZERO CORE CHANGES.**
> A plugin must be able to extend Cruhon without touching core files.
> Otherwise others cannot write their own library plugins.
> The discord plugin does everything via the **plugin API** (lexer_hook /
> lib_call / inject).

### 3.0 Freedom already exists — nested is just ergonomics

As long as `discord` is imported, 100% of discord.py is accessible today
via raw Python passthrough:

```clpy
@var[btn; discord.ui.Button(label="Click", style=discord.ButtonStyle.green)]
@var[v;   discord.ui.View()]
@raw
    v.add_item(btn)
@end
```

The only prerequisite for full Python freedom = **import guarantee** (3.2).
Nested namespace (`@discord.ui.Button[...]`) is the ergonomic shorthand.

### 3.1 Multi-level namespace (plugin-only, lexer_hook)

**Problem:** Lexer reads `@discord.method` as one level; `@discord.ui.Button`
breaks at the second dot.

**Solution (no core changes):** Extend the `_discord_preprocess` lexer_hook.
Only convert paths **containing a dot** via regex:

```
@discord.ui.Button[label="x"]
   ↓ lexer_hook  (regex: @discord.<path-with-dot>[ )
@discord.__nested["discord.ui.Button"; label="x"]
   ↓ registered lib_call("discord", "__nested", handler)
discord.ui.Button(label="x")
```

`__nested` handler: args[0] = path string, remaining args = real arguments →
emits `{path}({", ".join(rest)})`. Works in both inline (`@var`) and statement
context because it is a purely textual rewrite into a normal single-level lib call.

**Backward compatibility:** `@discord.send[...]` has no inner dot → regex
doesn't match; existing fallback emits `discord.send(...)` (actually special handler).
Block commands (`@_dc_on` etc.) don't start with `@discord.` so they're unaffected.

### 3.2 Import guarantee

`@discord.setup[...]` always injects:
```python
import discord
import asyncio
from discord.ext import commands
from discord.ext import tasks as __discord_tasks__
```
So `discord.ui.*`, `app_commands.*`, `commands.*`, `tasks.*` are always available.

---

## 4. LAYER 2 — Block Commands (interactive/complex parts)

Structures that can't be done in one line, requiring class + decorator + callback.

### 4.1 `@discord.view` — button/menu container
### 4.2 `@discord.button` (inside view) — button with callback
### 4.3 `@discord.select` — dropdown menu
### 4.4 `@discord.modal` — form/modal
### 4.5 `@discord.cog` — command group (modular bot)
### 4.6 `@discord.group` — slash command group

---

## 5. LAYER 1 — Shortcut Expansion (~60 → ~90)

Existing friendly commands are kept. High-use missing ones are added:

| Category | New shortcuts |
|---|---|
| Thread | `create_thread`, `archive_thread`, `add_thread_member` |
| Webhook | `create_webhook`, `send_webhook` |
| Invite | `create_invite`, `delete_invite` |
| Poll | `create_poll`, `end_poll` |
| Scheduled | `create_event`, `cancel_event` |
| Audit | `audit_logs` (last N records) |
| Files | `send_file`, `send_files` |
| Permissions | `set_permissions`, `sync_permissions` |
| Emoji/Sticker | `create_emoji`, `delete_emoji` |

---

## 6. Test Strategy

- **Transpile tests** (discord.py not required to be installed):
  verify generated Python code as a string.
- **Access matrix:** for each of the 253 classes in API_INVENTORY,
  check "can it be called from Cruhon?"
- **Example bots:** moderation, interactive buttons, modal forms, music (voice).
