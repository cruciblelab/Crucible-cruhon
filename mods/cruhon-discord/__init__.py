"""
cruhon-discord v1.4.0
======================
Discord bot plugin for Cruhon.
"Even people who don't know coding can quickly and easily do whatever they want."

━━━ BOT SETUP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.setup["TOKEN"]
  @discord.setup["TOKEN"; prefix="!"; intents="all"]
  @discord.run[]                       — start the bot (blocking)
  @discord.sync_commands[]             — sync slash commands with Discord

━━━ EVENT HANDLERS (block commands) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.on[ready]
  @discord.on[message; msg]
  @discord.on[join; member]            — member joined the server
  @discord.on[leave; member]           — member left the server
  @discord.on[reaction_add; reaction; user]
  @discord.on[reaction_remove; reaction; user]
  @discord.on[error; ctx; error]
  @discord.on[guild_join; guild]
  @discord.on[guild_leave; guild]
  @discord.on[message_edit; before; after]
  @discord.on[message_delete; message]
  ... (any discord.py event name works)

  @discord.command[ping; ctx]                       — prefix command (!ping)
  @discord.command[greet; ctx; user]                — command with parameters
  @discord.command[ban; ctx; member; perms="ban_members"; check=is_admin]
  @discord.hybrid[userinfo; ctx; member]            — BOTH prefix and slash
  @discord.slash[hello; "Says hello"; ctx]  — slash command (/hello)
  @discord.slash[roll; "Roll dice"; ctx; sides]
  @discord.task[cleanup; minutes=30]            — background task
  @discord.task[report; time="09:30"]           — daily at 09:30 UTC
  @discord.task[poll; seconds=30; wait_ready=True; count=5; reconnect=False]
  @discord.listen[message; msg]                 — additional event listener
  @discord.error_handler[ban; ctx; error]       — per-command error handler
      @discord.reply[ctx; f"Error: {error}"]
  @end

  Slash autocomplete (inside @discord.slash):
  @discord.slash[fruit; "Pick fruit"; interaction]
      @param[name; string; "Fruit"]
      @autocomplete[name]              — `current` holds the partial text
          @return[[discord.app_commands.Choice(name=x, value=x)
                   for x in FRUITS if current in x]]
      @end
      @discord.respond[interaction; name]
  @end

━━━ MESSAGING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.send[channel; "message"]
  @discord.send[channel; "message"; embed=my_embed]
  @discord.send_embed[channel; embed]
  @discord.reply[ctx; "message"]
  @discord.dm[user; "message"]
  @discord.respond[interaction; "message"]   — slash reply
  @discord.respond[interaction; "message"; ephemeral=True]
  @discord.send_modal[interaction; FeedbackModal]  — open a modal form
  @discord.defer[interaction]              — defer for slow operations
  @discord.followup[interaction; "message"] — send after defer
  @discord.edit[message; "new content"]
  @discord.edit_embed[message; embed]      — replace a message's embed
  @discord.dm_embed[user; embed]           — DM an embed
  @discord.delete[message]
  @discord.delete[message; delay=5]
  @discord.pin[message]
  @discord.unpin[message]
  @discord.process_commands[msg]          — process commands in on_message

━━━ REACTIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.react[message; "👍"]
  @discord.add_reactions[message; "👍"; "👎"; "❤️"]  — several at once
  @discord.unreact[message; "👍"; user]
  @discord.clear_reactions[message]

━━━ EMBED — QUICK (one-liner, all features) ━━━━━━━━━━━━━━━━━━━━━━
  Positional order: title ; description ; color ; footer ; image ; thumbnail ; author
  Empty string ""  skips that field

  @var[e; @embed["Title"; "Description"]]
  @var[e; @embed["Title"; "Description"; 0x3498db]]
  @var[e; @embed["Title"; "Description"; 0x3498db; "Footer"]]
  @var[e; @embed["Title"; "Description"; ""; "Footer"; "img.png"; "thumb.png"; "Author"]]

  With kwargs (can mix with positional):
  @var[e; @embed["Title"; "Description"; color=0xFF0000; footer="Footer"; author="Author"]]
  @var[e; @embed["Title"; "Description"; footer="Footer"; footer_icon="icon.png"]]
  @var[e; @embed["Title"; "Description"; author="Author"; author_icon="avatar.png"]]

  @discord.quick_embed — same as @embed, with @discord. prefix:
  @var[e; @discord.quick_embed["Title"; "Description"; footer="Footer"]]

━━━ EMBED — DETAILED (set fields individually) ━━━━━━━━━━━━━━━━━━━━
  @var[e; @discord.embed["Title"; "Description"]]
  @var[e; @discord.embed["Title"; "Description"; color=0xFF0000]]
  @discord.add_field[e; "Field Name"; "Field Value"]
  @discord.add_field[e; "Field Name"; "Field Value"; inline=False]
  @discord.set_footer[e; "Footer text"]
  @discord.set_footer[e; "Footer text"; icon="icon_url"]
  @discord.set_image[e; "image_url"]
  @discord.set_thumbnail[e; "thumbnail_url"]
  @discord.set_author[e; "Author Name"]
  @discord.set_author[e; "Author Name"; icon="avatar_url"]

━━━ MODERATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.ban[member]
  @discord.ban[member; reason="Spam"; delete_days=1]
  @discord.unban[guild; user]
  @discord.kick[member]
  @discord.kick[member; reason="Rule violation"]
  @discord.timeout[member; minutes=10]
  @discord.timeout[member; hours=1]
  @discord.untimeout[member]
  @discord.add_role[member; role]
  @discord.remove_role[member; role]
  @discord.nickname[member; "New Name"]

━━━ CHANNEL OPERATIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.purge[channel; 10]
  @discord.create_text[guild; "channel-name"]
  @discord.create_voice[guild; "voice-channel"]
  @discord.delete_channel[channel]
  @discord.lock_channel[channel]                — deny send_messages for @everyone
  @discord.lock_channel[channel; role]          — deny send_messages for a role
  @discord.unlock_channel[channel]              — restore send_messages for @everyone
  @discord.unlock_channel[channel; role]        — restore for a specific role

━━━ LOOKUP (inline expression) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @var[m; @discord.get_member[guild; 123456789]]
  @var[ch; @discord.get_channel[guild; 987654321]]
  @var[r; @discord.get_role[guild; "Admin"]]
  @var[u; @discord.find_member[guild; "username"]]
  @var[me; @discord.me[]]

━━━ PROTECTION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.ignore_self[msg]            — ignore the bot's own messages
  @discord.ignore_bots[msg]            — ignore all bot messages
  @discord.require_role[ctx; "Admin"] — stop if role is missing
  @discord.require_guild[]             — prevent DM usage

━━━ STATUS & MISC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.status["Playing a game"]
  @discord.status["Watching streams"; type="watching"]
  @discord.status["Listening to music"; type="listening"]
  @discord.log["message"]               — print with [bot] prefix
  @discord.wait_for["message"; timeout=30]
  @discord.wait_for["message"; timeout=30; check=my_check_fn]
  @discord.start_task[task_name]       — start a background task
  @discord.stop_task[task_name]        — stop a background task

━━━ UI COMPONENTS (block commands) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.view[ConfirmView; timeout=60]
      @discord.button[Yes; style=green]         — callback button
          @discord.respond[interaction; "✅"]
      @end
      @discord.button[Docs; url="https://..."]  — link button (no callback)
      @end
      @discord.user_select[Pick a user; min=1; max=1]  — typed selects:
          @body[interaction; selection] ... @end        — user / role / channel /
      @end                                              — mentionable_select
      @discord.select[Pick; min=1; max=1]  — string select (with @option)
          @option[Red; value=red] @option[Blue; value=blue]
          @body[interaction; selection] ... @end
      @end
  @end
  @discord.channel_select[Pick; channel_types=text,voice] — channel types filter
  @discord.modal[Feedback; FeedbackModal] ... @end
  @discord.cog[Moderation]                    — Cog (command group class)
      @discord.listen[ban; guild; user] ... @end   — event listener inside Cog
  @end
  @discord.group[admin; "Admin"] ... @end
  @discord.context_menu[Info; user] ... @end

━━━ INLINE CHECKS & FORMATTING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @if[@discord.has_role[member; "Admin"]]       — bool: has the role?
  @if[@discord.has_perm[member; ban_members]]   — bool: has the permission?
  @var[t; @discord.timestamp[dt; "R"]]    — Discord timestamp (<t:..:R>)
  @var[u; @discord.jump[message]]         — message.jump_url
  @var[a; @discord.avatar[user]]          — display avatar URL
  @var[e; @discord.escape[text]]          — escape markdown
  @var[m; @discord.user_mention[uid]]     — "<@id>" (also channel_/role_mention)
  @var[s; @discord.spoiler[text]]         — "||text||"
  @var[c; @discord.codeblock[code; py]]   — "```py\\n...\\n```"
  @var[p; @discord.progress[7; 10]]       — "▰▰▰▰▰▰▰▱▱▱" progress bar
  @var[u; @discord.oauth_url[]]           — bot invite URL

━━━ COLOR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @var[c; @discord.color["#3498db"]]     — from hex string
  @var[c; @discord.color[52; 152; 219]]  — from RGB
  @var[c; @discord.color[red]]           — named color (discord.Color.red())
  @var[c; @discord.color[3447003]]       — from decimal integer

━━━ VOICE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.join[voice_channel]              — join a voice channel
  @discord.leave[guild]                     — leave the voice channel
  @discord.play[guild; "song.mp3"]          — play audio (FFmpegPCMAudio)
  @discord.play[guild; source; volume=True] — with PCMVolumeTransformer
  @discord.stop_audio[guild]
  @discord.pause_audio[guild]
  @discord.resume_audio[guild]
  @discord.volume[guild; 0.5]              — requires PCMVolumeTransformer source
  @var[p; @discord.is_playing[guild]]       — bool: is audio playing?

━━━ EVENT COVERAGE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Short aliases (full list: _EVENT_MAP dict above):
    join / leave / ban / unban / member_update
    role_create / role_delete / role_update
    channel_create / channel_delete / channel_update
    bulk_delete / reaction_clear / typing
    thread_create / thread_delete / thread_update / thread_join
    invite_create / invite_delete
    stage_create / stage_update / stage_delete
    event_create / event_update / event_delete / event_user_add / event_user_remove
    poll_vote_add / poll_vote_remove / raw_poll_vote_add / raw_poll_vote_remove
    automod_action / automod_rule_create / automod_rule_update / automod_rule_delete

━━━ AUTOMOD RULE MANAGEMENT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.automod_keyword[guild; "name"; ["bad", "words"]]
      — shortcut: creates a keyword-block rule in one line
  @discord.create_automod_rule[guild; name=...; event_type=...; trigger=...; actions=...]
      — full control: all params passed as kwargs to guild.create_automod_rule()
  @discord.edit_automod_rule[rule; name=...; enabled=True; actions=...]
  @discord.delete_automod_rule[rule]
  @discord.fetch_automod_rules[guild]           — returns list of AutoModRule

━━━ SOUNDBOARD (discord.py ≥ 2.4) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.fetch_soundboard_sounds[guild]
  @discord.create_soundboard_sound[guild; "name"; sound_bytes]
  @discord.create_soundboard_sound[guild; "name"; sound_bytes; volume=1.0; emoji_name="🔊"]
  @discord.edit_soundboard_sound[sound; name=...; volume=...; emoji_id=...]
  @discord.delete_soundboard_sound[sound]
    app_error (app_command_error)
    connect / disconnect / resumed / shard_ready
    raw_reaction_add / raw_reaction_remove / raw_reaction_clear
    raw_message_delete / raw_message_edit / raw_typing / raw_thread_update
    Any unknown name → passed through as-is: on_<name>
"""

from __future__ import annotations

import ast
import re


# ─────────────────────────────────────────────────────────────
# BLOCK COMMANDS — rewritten by lexer hook before tokenization
# ─────────────────────────────────────────────────────────────

_BLOCK_CMDS = {"on", "command", "hybrid", "slash", "task", "listen",
               "view", "button", "cog", "group", "modal",
               "select", "user_select", "role_select", "channel_select", "mentionable_select",
               "context_menu", "error_handler"}

# Friendly button style names → discord.ButtonStyle member (comprehensive)
_BUTTON_STYLES = {
    "primary": "primary", "blurple": "primary", "blue": "primary",
    "secondary": "secondary", "grey": "secondary", "gray": "secondary",
    "success": "success", "green": "success",
    "danger": "danger", "red": "danger",
    "link": "link", "url": "link",
}


def _slug(s: str) -> str:
    """Produce a valid Python identifier from a label string (button method name)."""
    s = (s or "").strip().strip("\"'")
    s = re.sub(r"\W+", "_", s, flags=re.UNICODE).strip("_").lower()
    if not s or not (s[0].isalpha() or s[0] == "_"):
        s = "btn_" + s
    return s or "button"


def _looks_like_expr(a: str) -> bool:
    """
    True for a bare (unquoted) arg that is a real Python expression — a
    variable name, an attribute/subscript/call chain, even arbitrarily
    nested calls like str(ctx.guild.created_at.date()) or
    any(w in content for w in banned_words). Requires an identifier-like
    start (excludes bare numbers/dates such as "2024-01-01", which stay
    literal text) and must parse as a valid Python expression — plain
    multi-word text ("My Webhook") isn't valid Python and correctly
    fails, which is exactly the "non-coder bare text" case _as_str
    exists to support.
    """
    if not a or not (a[0].isalpha() or a[0] == "_"):
        return False
    try:
        ast.parse(a, mode="eval")
    except SyntaxError:
        return False
    return True


def _as_str(a: str) -> str:
    """
    Display text argument → string literal / f-string / expression.

      "already quoted"        → passed through as-is
      f"already an f-string"  → passed through as-is
      "quoted with {braces}"  → upgraded to an f-string (interpolated)
      bare_variable_name      → passed through as a Python expression
                                 (variable reference), NOT stringified —
                                 this is what lets @discord.reply[ctx; msg]
                                 or @discord.create_webhook[ch; name] work
                                 with a caller's own variable/parameter.
      member.name / ctx.guild.name / fn()
                               → same: real expressions pass through.
      Bare text (multiple words, not valid Python) → repr()'d as a
      literal string — the original non-coder-friendly behavior.
    """
    a = (a or "").strip()
    if not a:
        return '""'
    if a[:2] in ('f"', "f'"):
        return a
    if a[:1] in ('"', "'") and len(a) >= 2:
        inner = a[1:-1]
        if "{" in inner and "}" in inner:
            return f"f{a}"
        return a
    if _looks_like_expr(a):
        return a
    return repr(a)


def _style_expr(raw: str) -> str:
    """style=green → discord.ButtonStyle.success (unknown → pass through)."""
    key = raw.strip().strip("\"'").lower()
    member = _BUTTON_STYLES.get(key)
    if member:
        return f"discord.ButtonStyle.{member}"
    # User already wrote discord.ButtonStyle.X or unknown name
    return raw.strip() if "." in raw else f"discord.ButtonStyle.{key}"

# Nested namespace: @discord.ui.Button[  /  @discord.utils.get[  /  @discord.Color.blue[
# Matches @discord. followed by 2+ dotted segments, then "[".
# Single-level (@discord.send[) has no inner dot → not matched.
_NESTED_RE = re.compile(r"@discord\.([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)\[")

# Friendly event names → discord.py event function names.
# Any name NOT in this map is passed through as-is:
#   @discord.on[my_custom_event; data] → async def on_my_custom_event(data):
_EVENT_MAP = {
    # ── Core ─────────────────────────────────────────────────────
    "ready":                    "ready",
    "message":                  "message",
    "error":                    "command_error",
    "app_error":                "app_command_error",
    "slash_error":              "app_command_error",
    # ── Member ───────────────────────────────────────────────────
    "join":                     "member_join",
    "leave":                    "member_remove",
    "member_join":              "member_join",
    "member_remove":            "member_remove",
    "member_update":            "member_update",
    "ban":                      "member_ban",
    "unban":                    "member_unban",
    "user_update":              "user_update",
    "presence":                 "presence_update",
    "presence_update":          "presence_update",
    # ── Message ──────────────────────────────────────────────────
    "message_edit":             "message_edit",
    "message_delete":           "message_delete",
    "bulk_delete":              "bulk_message_delete",
    "message_bulk_delete":      "bulk_message_delete",
    "raw_message_delete":       "raw_message_delete",
    "raw_message_edit":         "raw_message_edit",
    # ── Reaction ─────────────────────────────────────────────────
    "reaction_add":             "reaction_add",
    "reaction_remove":          "reaction_remove",
    "reaction_clear":           "reaction_clear",
    "reaction_clear_emoji":     "reaction_clear_emoji",
    "raw_reaction_add":         "raw_reaction_add",
    "raw_reaction_remove":      "raw_reaction_remove",
    "raw_reaction_clear":       "raw_reaction_clear",
    "raw_reaction_clear_emoji": "raw_reaction_clear_emoji",
    # ── Typing ───────────────────────────────────────────────────
    "typing":                   "typing",
    "raw_typing":               "raw_typing",
    # ── Guild ────────────────────────────────────────────────────
    "guild_join":               "guild_join",
    "guild_leave":              "guild_remove",
    "guild_update":             "guild_update",
    "guild_available":          "guild_available",
    "guild_unavailable":        "guild_unavailable",
    # ── Role ─────────────────────────────────────────────────────
    "role_create":              "guild_role_create",
    "role_delete":              "guild_role_delete",
    "role_update":              "guild_role_update",
    # ── Channel ──────────────────────────────────────────────────
    "channel_create":           "guild_channel_create",
    "channel_delete":           "guild_channel_delete",
    "channel_update":           "guild_channel_update",
    "channel_pins_update":      "guild_channel_pins_update",
    # ── Thread ───────────────────────────────────────────────────
    "thread_create":            "thread_create",
    "thread_delete":            "thread_delete",
    "thread_update":            "thread_update",
    "thread_join":              "thread_join",
    "thread_remove":            "thread_remove",
    "thread_member_join":       "thread_member_join",
    "thread_member_remove":     "thread_member_remove",
    "raw_thread_update":        "raw_thread_update",
    "raw_thread_delete":        "raw_thread_delete",
    # ── Invite ───────────────────────────────────────────────────
    "invite_create":            "invite_create",
    "invite_delete":            "invite_delete",
    # ── Voice ────────────────────────────────────────────────────
    "voice":                    "voice_state_update",
    "voice_state_update":       "voice_state_update",
    "voice_channel_status_update": "voice_channel_status_update",
    # ── Stage ────────────────────────────────────────────────────
    "stage_create":             "stage_instance_create",
    "stage_update":             "stage_instance_update",
    "stage_delete":             "stage_instance_delete",
    # ── Scheduled events ─────────────────────────────────────────
    "event_create":             "scheduled_event_create",
    "event_update":             "scheduled_event_update",
    "event_delete":             "scheduled_event_delete",
    "event_user_add":           "scheduled_event_user_add",
    "event_user_remove":        "scheduled_event_user_remove",
    # ── Poll ─────────────────────────────────────────────────────
    "poll_vote_add":            "poll_vote_add",
    "poll_vote_remove":         "poll_vote_remove",
    "raw_poll_vote_add":        "raw_poll_vote_add",
    "raw_poll_vote_remove":     "raw_poll_vote_remove",
    # ── AutoMod ──────────────────────────────────────────────────
    "automod_action":           "automod_action",
    "automod_rule_create":      "automod_rule_create",
    "automod_rule_update":      "automod_rule_update",
    "automod_rule_delete":      "automod_rule_delete",
    # ── Emoji / Sticker ──────────────────────────────────────────
    "emojis_update":            "guild_emojis_update",
    "stickers_update":          "guild_stickers_update",
    # ── Webhook / Integration ────────────────────────────────────
    "webhooks_update":          "webhooks_update",
    "integration_create":       "integration_create",
    "integration_update":       "integration_update",
    "integration_delete":       "integration_delete",
    # ── Entitlement (premium) ────────────────────────────────────
    "entitlement_create":       "entitlement_create",
    "entitlement_update":       "entitlement_update",
    "entitlement_delete":       "entitlement_delete",
    # ── Interaction ──────────────────────────────────────────────
    "interaction":              "interaction",
    # ── Connection / Shard ───────────────────────────────────────
    "connect":                  "connect",
    "disconnect":               "disconnect",
    "resumed":                  "resumed",
    "shard_ready":              "shard_ready",
    "shard_connect":            "shard_connect",
    "shard_disconnect":         "shard_disconnect",
    "shard_resumed":            "shard_resumed",
}


def _discord_preprocess(source: str) -> str:
    """
    Lexer pre-hook (runs on raw source before tokenization). Two rewrites:

    1) Block commands:  @discord.on[ → @_dc_on[
       so they hit the AT_CMD branch of the parser.

    2) Nested namespace passthrough (FULL discord.py freedom, no core changes):
       @discord.ui.Button[label="x"]
         → @discord.__nested["discord.ui.Button"; label="x"]
       The __nested lib_call handler then emits  discord.ui.Button(label="x").
       Works in both statement and inline (@var) context because it is a
       purely textual rewrite into a normal single-level lib call.
    """
    # 1) Block commands first (so nested regex never touches them)
    for cmd in _BLOCK_CMDS:
        source = source.replace(f"@discord.{cmd}[", f"@_dc_{cmd}[")

    # 2) Nested dotted paths → __nested call carrying the full path as a string
    def _repl(m: "re.Match") -> str:
        path = "discord." + m.group(1)
        return f'@discord.__nested["{path}"; '

    source = _NESTED_RE.sub(_repl, source)

    # Empty-arg case:  @discord.__nested["path"; ]  →  @discord.__nested["path"]
    source = re.sub(r'(@discord\.__nested\["[^"]+");\s*\]', r"\1]", source)

    return source


# ─────────────────────────────────────────────────────────────
# BLOCK VISITORS
# ─────────────────────────────────────────────────────────────

def _visit_dc_on(transpiler, node):
    """
    @discord.on[ready]
    @discord.on[message; msg]
    @discord.on[join; member]
    → @__bot__.event + async def on_<event>(<params>):
    """
    event = node.args[0].strip() if node.args else "ready"
    params = [a.strip() for a in node.args[1:]]

    event_name = _EVENT_MAP.get(event, event)
    params_str = ", ".join(params)

    indent = "    " * transpiler._indent
    body_code = transpiler._block(node.body)

    lines = [
        f"{indent}@__bot__.event",
        f"{indent}async def on_{event_name}({params_str}):",
        body_code if body_code.strip() else f"{indent}    pass",
    ]

    # Auto-inject process_commands for message event so text commands keep working
    if event in ("message", "on_message") and params:
        msg_var = params[0]
        lines.append(f"{indent}    await __bot__.process_commands({msg_var})")

    return "\n".join(lines)


def _check_decorators(kwargs, indent, mode="command"):
    """cooldown= / perms= / guild_only= / owner_only= → emit check decorator lines."""
    out = []
    if "cooldown" in kwargs:
        n = kwargs["cooldown"].strip()
        if mode == "slash":
            out.append(f"{indent}@discord.app_commands.checks.cooldown(1, {n})")
        else:
            out.append(f"{indent}@commands.cooldown(1, {n}, commands.BucketType.user)")
    if "perms" in kwargs:
        raw = kwargs["perms"].strip().strip("\"'")
        perms = ", ".join(f"{p.strip()}=True" for p in raw.split(",") if p.strip())
        if mode == "slash":
            out.append(f"{indent}@discord.app_commands.checks.has_permissions({perms})")
        else:
            out.append(f"{indent}@commands.has_permissions({perms})")
    if kwargs.get("guild_only", "").strip() in ("True", "true", "1"):
        if mode == "slash":
            out.append(f"{indent}@discord.app_commands.guild_only()")
        else:
            out.append(f"{indent}@commands.guild_only()")
    if kwargs.get("owner_only", "").strip() in ("True", "true", "1") and mode != "slash":
        out.append(f"{indent}@commands.is_owner()")
    if "check" in kwargs:
        fn = kwargs["check"].strip()
        if mode == "slash":
            out.append(f"{indent}@discord.app_commands.check({fn})")
        else:
            out.append(f"{indent}@commands.check({fn})")
    return out


def _visit_dc_command(transpiler, node):
    """
    @discord.command[ping; ctx]
    @discord.command[greet; ctx; user; aliases="hi,hey"]
    @discord.command[ban; ctx; member; perms="ban_members"; cooldown=5]
    → @__bot__.command(name=...) + check decorators + async def <name>(ctx, ...):
    """
    args = node.args
    kwargs = node.kwargs

    name = args[0].strip() if args else "my_command"
    ctx = args[1].strip() if len(args) > 1 else "ctx"
    extra_params = [a.strip() for a in args[2:]]
    params_str = ", ".join([ctx] + extra_params)

    # Build decorator kwargs from node.kwargs
    dec_kw_parts = []
    if "aliases" in kwargs:
        raw = kwargs["aliases"].strip().strip('"\'')
        alias_list = ", ".join(f'"{a.strip()}"' for a in raw.split(","))
        dec_kw_parts.append(f"aliases=[{alias_list}]")
    if "brief" in kwargs:
        dec_kw_parts.append(f"brief={kwargs['brief']}")
    if "description" in kwargs:
        dec_kw_parts.append(f"description={kwargs['description']}")
    dec_kw = (", " + ", ".join(dec_kw_parts)) if dec_kw_parts else ""

    indent = "    " * transpiler._indent
    body_code = transpiler._block(node.body)

    lines = [
        f"{indent}@__bot__.command(name={name!r}{dec_kw})",
        *_check_decorators(kwargs, indent, "command"),
        f"{indent}async def {name}({params_str}):",
        body_code if body_code.strip() else f"{indent}    pass",
    ]
    return "\n".join(lines)


def _visit_dc_hybrid(transpiler, node):
    """
    @discord.hybrid[userinfo; ctx; member]
    @discord.hybrid[ban; ctx; member; description="Ban a user"; perms="ban_members"]
    → @__bot__.hybrid_command(...) — works as BOTH a prefix and a slash command.
    """
    args = node.args
    kwargs = node.kwargs

    name = args[0].strip() if args else "my_command"
    ctx = args[1].strip() if len(args) > 1 else "ctx"
    extra_params = [a.strip() for a in args[2:]]
    params_str = ", ".join([ctx] + extra_params)

    dec_kw_parts = []
    if "aliases" in kwargs:
        raw = kwargs["aliases"].strip().strip('"\'')
        alias_list = ", ".join(f'"{a.strip()}"' for a in raw.split(","))
        dec_kw_parts.append(f"aliases=[{alias_list}]")
    if "description" in kwargs:
        dec_kw_parts.append(f"description={kwargs['description']}")
    if "with_app_command" in kwargs:
        dec_kw_parts.append(f"with_app_command={kwargs['with_app_command'].strip()}")
    dec_kw = (", " + ", ".join(dec_kw_parts)) if dec_kw_parts else ""

    indent = "    " * transpiler._indent
    body_code = transpiler._block(node.body)

    lines = [
        f"{indent}@__bot__.hybrid_command(name={name!r}{dec_kw})",
        *_check_decorators(kwargs, indent, "command"),
        f"{indent}async def {name}({params_str}):",
        body_code if body_code.strip() else f"{indent}    pass",
    ]
    return "\n".join(lines)


# Slash option type names → Python annotation
_OPTION_TYPES = {
    "string": "str", "str": "str", "text": "str",
    "int": "int", "integer": "int", "number": "float", "float": "float",
    "bool": "bool", "boolean": "bool",
    "user": "discord.Member", "member": "discord.Member",
    "channel": "discord.TextChannel", "voice": "discord.VoiceChannel",
    "role": "discord.Role", "mentionable": "discord.abc.Mentionable",
    "attachment": "discord.Attachment", "file": "discord.Attachment",
}


def _val(v: str) -> str:
    """Choice value → keep if quoted/numeric, else make it a string literal."""
    v = v.strip()
    if v[:1] in ('"', "'"):
        return v
    if v.replace(".", "", 1).lstrip("-").isdigit():
        return v
    return repr(v)


def _parse_slash_config(node):
    """
    Split a slash command body into option config and real body.
    Returns (typed_params, describes, choices, autocompletes, body_children).
    Shared by @discord.slash and @discord.group subcommands.
    """
    from cruhon.core.ast_nodes import PluginBlockNode

    typed_params = []     # (pname, anno, required)
    describes = {}        # pname -> description expr
    choices = {}          # pname -> [(label, value), ...]
    autocompletes = []    # (pname, body_nodes)
    body_children = []
    for child in node.body:
        if isinstance(child, PluginBlockNode) and child.plugin_name == "autocomplete":
            apname = child.args[0].strip() if child.args else "option"
            autocompletes.append((apname, child.body))
        elif isinstance(child, PluginBlockNode) and child.plugin_name == "_dc_param":
            pa, pk = child.args, child.kwargs
            pname = pa[0].strip()
            tkey = (pa[1].strip().strip("\"'").lower()) if len(pa) > 1 else "string"
            anno = _OPTION_TYPES.get(tkey, "str")
            required = True
            if len(pa) > 3 and pa[3].strip().strip("\"'").lower() in ("optional", "false"):
                required = False
            if pk.get("required", "").strip() in ("False", "false", "0"):
                required = False
            desc = None
            if len(pa) > 2:
                desc = pa[2].strip()
            if "description" in pk:
                desc = pk["description"].strip()
            if desc:
                describes[pname] = desc if desc[:1] in ('"', "'") else _as_str(desc)
            typed_params.append((pname, anno, required))
        elif isinstance(child, PluginBlockNode) and child.plugin_name == "_dc_choice":
            ca = child.args
            cname = ca[0].strip() if ca else "opt"
            clist = []
            for item in ca[1:]:
                item = item.strip()
                if "=" in item and item.split("=")[0].strip().isidentifier():
                    lbl, vv = item.split("=", 1)
                    clist.append((lbl.strip(), vv.strip()))
                else:
                    clist.append((item.strip("\"'"), item))
            for k, vv in child.kwargs.items():
                clist.append((k, vv.strip()))
            choices[cname] = clist
        else:
            body_children.append(child)
    return typed_params, describes, choices, autocompletes, body_children


def _render_slash(transpiler, node, target="__bot__.tree"):
    """
    Render a slash command. `target` is the decorator owner:
    "__bot__.tree" for top-level, the group variable name for group subcommands.

    Basic:
      @discord.slash[hello; "Say hi"; interaction]
      @discord.slash[roll; "Roll dice"; interaction; sides]

    With typed options and choices:
      @discord.slash[ban; "Ban a user"; interaction]
          @param[member; user; "User to ban"]            # required by default
          @param[reason; string; "Reason"; optional]     # optional
          @choice[reason; Spam=spam; Abuse=abuse]        # restrict choices
          @discord.respond[interaction; f"Banned {member}"]
      @end

    Emits @<target>.command + @describe + @choices + typed signature.
    """
    args = node.args
    kwargs = node.kwargs
    name = args[0].strip() if args else "slash_cmd"
    description = args[1].strip() if len(args) > 1 else f'"{args[0].strip() if args else "command"}"'
    ctx = args[2].strip() if len(args) > 2 else "interaction"
    extra_params = [a.strip() for a in args[3:]]

    indent = "    " * transpiler._indent

    typed_params, describes, choices, autocompletes, body_children = _parse_slash_config(node)

    # Build signature: ctx, untyped positional params, then typed params
    sig = [ctx] + extra_params
    for pname, anno, required in typed_params:
        sig.append(f"{pname}: {anno}" if required else f"{pname}: {anno} = None")

    # Decorators
    deco = [f"{indent}@{target}.command(name={name!r}, description={description})"]
    deco += _check_decorators(kwargs, indent, "slash")
    if describes:
        parts = ", ".join(f"{n}={d}" for n, d in describes.items())
        deco.append(f"{indent}@discord.app_commands.describe({parts})")
    for cname, clist in choices.items():
        # Choice labels (from `Label=value` pairs in @choice[...]) are always
        # literal display text, never a variable reference — unlike _as_str's
        # general rule, a bare identifier-shaped label here still means the
        # literal word, so it's repr()'d directly rather than passed through.
        items = ", ".join(
            f"discord.app_commands.Choice(name={l!r}, value={_val(v)})"
            for l, v in clist
        )
        deco.append(f"{indent}@discord.app_commands.choices({cname}=[{items}])")

    # Render command body (only the non-config children)
    saved = transpiler._indent
    transpiler._indent += 1
    body_code = "\n".join(
        filter(None, (n.accept(transpiler) for n in body_children))
    )
    transpiler._indent = saved

    lines = deco + [
        f"{indent}async def {name}({', '.join(sig)}):",
        body_code if body_code.strip() else f"{indent}    pass",
    ]

    # Autocomplete callbacks: @<name>.autocomplete("<param>") + async def
    # `interaction` and `current` (the partial text) are available in the body.
    for apname, abody in autocompletes:
        saved = transpiler._indent
        transpiler._indent += 1
        acode = "\n".join(filter(None, (n.accept(transpiler) for n in abody)))
        transpiler._indent = saved
        lines.append(f"{indent}@{name}.autocomplete({apname!r})")
        lines.append(f"{indent}async def {name}_{apname}_autocomplete(interaction, current: str):")
        lines.append(acode if acode.strip() else f"{indent}    pass")

    return "\n".join(lines)


def _visit_dc_slash(transpiler, node):
    """Top-level @discord.slash → @__bot__.tree.command."""
    return _render_slash(transpiler, node, "__bot__.tree")


def _visit_dc_context_menu(transpiler, node):
    """
    @discord.context_menu[Info; user]      (type: user | message)
        @discord.respond[interaction; f"{target}"]
    @end
    → @__bot__.tree.context_menu(name=...) + async def(interaction, target: Type):
    """
    args = node.args
    label = _as_str(args[0]) if args else '"Command"'
    fname = _slug(args[0] if args else "context")
    ctype = (args[1].strip().strip("\"'").lower()) if len(args) > 1 else "user"
    target_type = "discord.Message" if ctype in ("message", "msg") else "discord.Member"

    indent = "    " * transpiler._indent
    body_code = transpiler._block(node.body)
    return "\n".join([
        f"{indent}@__bot__.tree.context_menu(name={label})",
        f"{indent}async def {fname}(interaction: discord.Interaction, target: {target_type}):",
        body_code if body_code.strip() else f"{indent}    pass",
    ])


def _visit_dc_task(transpiler, node):
    """
    @discord.task[cleanup; minutes=30]
    @discord.task[heartbeat; seconds=10]
    @discord.task[daily_report; time="09:30"]      — run daily at 09:30 (UTC)
    @discord.task[once; minutes=1; count=5]        — stop after 5 runs
    @discord.task[poller; seconds=30; wait_ready=True] — wait until bot is ready
    → @__discord_tasks__.loop(...) + async def <name>():
      (+ before_loop waiting for ready when wait_ready=True)
    """
    args = node.args
    kwargs = node.kwargs

    func_name = args[0].strip() if args else "background_task"

    # Time interval — kwarg takes priority, then second positional arg (minutes)
    if "time" in kwargs:
        # time="09:30" → daily at that wall-clock time (UTC)
        raw = kwargs["time"].strip().strip("\"'")
        hh, _, mm = raw.partition(":")
        loop_kw = (f"time=__import__('datetime').time("
                   f"hour={int(hh) if hh.isdigit() else 0}, "
                   f"minute={int(mm) if mm.isdigit() else 0}, "
                   f"tzinfo=__import__('datetime').timezone.utc)")
    elif "minutes" in kwargs:
        loop_kw = f"minutes={kwargs['minutes']}"
    elif "seconds" in kwargs:
        loop_kw = f"seconds={kwargs['seconds']}"
    elif "hours" in kwargs:
        loop_kw = f"hours={kwargs['hours']}"
    elif len(args) > 1:
        loop_kw = f"minutes={args[1].strip()}"
    else:
        loop_kw = "minutes=5"

    extra_loop = []
    if "count" in kwargs:
        extra_loop.append(f"count={kwargs['count'].strip()}")
    if "reconnect" in kwargs:
        extra_loop.append(f"reconnect={kwargs['reconnect'].strip()}")
    loop_args = ", ".join([loop_kw] + extra_loop)

    indent = "    " * transpiler._indent
    body_code = transpiler._block(node.body)

    lines = [
        f"{indent}@__discord_tasks__.loop({loop_args})",
        f"{indent}async def {func_name}():",
        body_code if body_code.strip() else f"{indent}    pass",
    ]

    # wait_ready=True → don't start ticking until the bot is connected
    if kwargs.get("wait_ready", "").strip() in ("True", "true", "1"):
        lines.append(f"{indent}@{func_name}.before_loop")
        lines.append(f"{indent}async def __{func_name}_before():")
        lines.append(f"{indent}    await __bot__.wait_until_ready()")

    return "\n".join(lines)


def _visit_dc_error_handler(transpiler, node):
    """
    @discord.error_handler[ban; ctx; error]      — per-command error handler
        @discord.reply[ctx; f"Error: {error}"]
    @end
    → @ban.error + async def ban_error(ctx, error):
    Works for both prefix commands and slash commands (same decorator name).
    """
    args = node.args
    cmd = args[0].strip() if args else "command"
    params = [a.strip() for a in args[1:]] or ["ctx", "error"]

    indent = "    " * transpiler._indent
    body_code = transpiler._block(node.body)
    return "\n".join([
        f"{indent}@{cmd}.error",
        f"{indent}async def {cmd}_error({', '.join(params)}):",
        body_code if body_code.strip() else f"{indent}    pass",
    ])


def _visit_dc_listen(transpiler, node):
    """
    @discord.listen[message; msg]
    → @__bot__.listen() + async def on_<event>(<params>):
    """
    event = node.args[0].strip() if node.args else "message"
    params = [a.strip() for a in node.args[1:]]

    event_name = _EVENT_MAP.get(event, event)
    params_str = ", ".join(params)

    indent = "    " * transpiler._indent
    body_code = transpiler._block(node.body)

    lines = [
        f"{indent}@__bot__.listen()",
        f"{indent}async def on_{event_name}({params_str}):",
        body_code if body_code.strip() else f"{indent}    pass",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# UI BLOCK VISITORS — View / Button (interactive components)
# ─────────────────────────────────────────────────────────────

def _is_link_button(btn) -> bool:
    """A button with a url= is a link button — it has no callback."""
    return "url" in btn.kwargs


def _link_button_item(btn) -> str:
    """
    @discord.button[Docs; url="https://..."; emoji="📖"; row=0]
    → discord.ui.Button(label=..., url=..., style=discord.ButtonStyle.link, ...)
    Link buttons have no callback, so a view adds them via self.add_item(...).
    """
    args = btn.args
    kw = btn.kwargs
    label = _as_str(args[0]) if args else '"Link"'
    parts = [f"label={label}", "style=discord.ButtonStyle.link", f"url={kw['url'].strip()}"]
    if "emoji" in kw:
        parts.append(f"emoji={kw['emoji'].strip()}")
    if "row" in kw:
        parts.append(f"row={kw['row'].strip()}")
    if "disabled" in kw:
        parts.append(f"disabled={kw['disabled'].strip()}")
    return f"discord.ui.Button({', '.join(parts)})"


def _render_button(transpiler, btn):
    """
    @discord.button[Confirm; style=green; emoji="✅"; row=0]
        <callback body>
    @end
    → @discord.ui.button(...) + async def <slug>(self, interaction, button):
    `interaction` is available inside the callback body.

    Link buttons (url=) have no callback in discord.py; when used standalone
    they are emitted as a bare Button expression.
    """
    if _is_link_button(btn):
        base = "    " * transpiler._indent
        return f"{base}{_link_button_item(btn)}"

    args = btn.args
    kw = btn.kwargs
    label = _as_str(args[0]) if args else '"Button"'
    name = _slug(args[0] if args else 'button')

    deco = [f"label={label}"]
    if "style" in kw:
        deco.append(f"style={_style_expr(kw['style'])}")
    if "emoji" in kw:
        deco.append(f"emoji={kw['emoji'].strip()}")
    if "row" in kw:
        deco.append(f"row={kw['row'].strip()}")
    if "custom_id" in kw:
        deco.append(f"custom_id={kw['custom_id'].strip()}")
    if "disabled" in kw:
        deco.append(f"disabled={kw['disabled'].strip()}")

    base = "    " * transpiler._indent
    body_code = transpiler._block(btn.body)  # render at _indent+1 level
    return "\n".join([
        f"{base}@discord.ui.button({', '.join(deco)})",
        f"{base}async def {name}(self, interaction, button):",
        body_code if body_code.strip() else f"{base}    pass",
    ])


def _visit_dc_button(transpiler, node):
    """Standalone @discord.button — emits a method in a class body context."""
    return _render_button(transpiler, node)


def _visit_dc_view(transpiler, node):
    """
    @discord.view[ConfirmView; timeout=60]
        @discord.button[...] ... @end
    @end
    → class ConfirmView(discord.ui.View): __init__ + button methods
    """
    from cruhon.core.ast_nodes import PluginBlockNode

    name = (node.args[0].strip().strip("\"'")) if node.args else "MyView"
    timeout = node.kwargs.get("timeout", "180").strip()
    # persistent=True → timeout=None (register with @discord.add_view at startup;
    # buttons should carry a custom_id so they survive restarts)
    if node.kwargs.get("persistent", "").strip() in ("True", "true", "1"):
        timeout = "None"

    base = "    " * transpiler._indent

    # Link buttons (url=) have no callback → added in __init__ via add_item
    link_buttons = [
        c for c in node.body
        if isinstance(c, PluginBlockNode) and c.plugin_name == "_dc_button"
        and _is_link_button(c)
    ]

    lines = [
        f"{base}class {name}(discord.ui.View):",
        f"{base}    def __init__(self):",
        f"{base}        super().__init__(timeout={timeout})",
    ]
    for lb in link_buttons:
        lines.append(f"{base}        self.add_item({_link_button_item(lb)})")

    transpiler._indent += 1  # class body indentation level
    try:
        for child in node.body:
            if isinstance(child, PluginBlockNode) and child.plugin_name == "_dc_button":
                if _is_link_button(child):
                    continue  # already added in __init__
                lines.append(_render_button(transpiler, child))
            elif isinstance(child, PluginBlockNode) and child.plugin_name in _ALL_SELECT_NAMES:
                lines.append(_render_any_select(transpiler, child))
            else:
                rendered = child.accept(transpiler)
                if rendered:
                    lines.append(rendered)
    finally:
        transpiler._indent -= 1

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# COG BLOCK VISITOR — modular bot (command group class)
# ─────────────────────────────────────────────────────────────

def _render_cog_method(transpiler, child):
    """
    Inside a Cog body: render @discord.command / @discord.slash /
    @discord.hybrid / @discord.listen as class methods.
    """
    args = child.args
    kw = child.kwargs
    base = "    " * transpiler._indent

    if child.plugin_name == "_dc_command":
        name = args[0].strip() if args else "cmd"
        ctx = args[1].strip() if len(args) > 1 else "ctx"
        extra = [a.strip() for a in args[2:]]
        params = ", ".join(["self", ctx] + extra)
        body_code = transpiler._block(child.body)
        return "\n".join([
            f"{base}@commands.command(name={name!r})",
            *_check_decorators(kw, base, "command"),
            f"{base}async def {name}({params}):",
            body_code if body_code.strip() else f"{base}    pass",
        ])

    if child.plugin_name == "_dc_hybrid":
        name = args[0].strip() if args else "cmd"
        ctx = args[1].strip() if len(args) > 1 else "ctx"
        extra = [a.strip() for a in args[2:]]
        params = ", ".join(["self", ctx] + extra)
        desc_kw = (f", description={kw['description']}") if "description" in kw else ""
        body_code = transpiler._block(child.body)
        return "\n".join([
            f"{base}@commands.hybrid_command(name={name!r}{desc_kw})",
            *_check_decorators(kw, base, "command"),
            f"{base}async def {name}({params}):",
            body_code if body_code.strip() else f"{base}    pass",
        ])

    if child.plugin_name == "_dc_slash":
        name = args[0].strip() if args else "cmd"
        desc = args[1].strip() if len(args) > 1 else repr(name)
        ctx = args[2].strip() if len(args) > 2 else "interaction"
        extra = [a.strip() for a in args[3:]]
        params = ", ".join(["self", ctx] + extra)
        body_code = transpiler._block(child.body)
        return "\n".join([
            f"{base}@discord.app_commands.command(name={name!r}, description={desc})",
            *_check_decorators(kw, base, "slash"),
            f"{base}async def {name}({params}):",
            body_code if body_code.strip() else f"{base}    pass",
        ])

    if child.plugin_name == "_dc_listen":
        event = args[0].strip() if args else "message"
        params = [a.strip() for a in args[1:]]
        event_name = _EVENT_MAP.get(event, event)
        params_str = ", ".join(["self"] + params)
        body_code = transpiler._block(child.body)
        return "\n".join([
            f"{base}@commands.Cog.listener()",
            f"{base}async def on_{event_name}({params_str}):",
            body_code if body_code.strip() else f"{base}    pass",
        ])

    # Render other nodes as-is
    return child.accept(transpiler)


def _visit_dc_cog(transpiler, node):
    """
    @discord.cog[Moderation]
        @discord.command[ban; ctx; member] ... @end
    @end
    → class Moderation(commands.Cog): __init__(self, bot) + methods
    Register with: @discord.add_cog[Moderation] (call from on_ready/setup).
    """
    name = (node.args[0].strip().strip("\"'")) if node.args else "MyCog"
    base = "    " * transpiler._indent
    lines = [
        f"{base}class {name}(commands.Cog):",
        f"{base}    def __init__(self, bot):",
        f"{base}        self.bot = bot",
    ]
    transpiler._indent += 1
    try:
        for child in node.body:
            rendered = _render_cog_method(transpiler, child)
            if rendered:
                lines.append(rendered)
    finally:
        transpiler._indent -= 1
    return "\n".join(lines)


def _visit_dc_group(transpiler, node):
    """
    @discord.group[admin; "Admin commands"]
        @discord.slash[ban; "Ban a user"; interaction; member] ... @end
    @end
    → app_commands.Group subclass + sub-command methods.
    """
    name = (node.args[0].strip().strip("\"'")) if node.args else "MyGroup"
    desc = node.args[1].strip() if len(node.args) > 1 else repr(name)
    cls = name.capitalize() + "Group"
    base = "    " * transpiler._indent
    lines = [
        f"{base}class {cls}(discord.app_commands.Group):",
        f"{base}    pass",
        f"{base}{name} = {cls}(name={name!r}, description={desc})",
    ]
    # Bind sub-commands with the @<group>.command decorator — full slash
    # rendering, so @param / @choice / @autocomplete work inside groups too.
    for child in node.body:
        if isinstance(child, type(node)) and child.plugin_name == "_dc_slash":
            lines.append(_render_slash(transpiler, child, name))
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# SUB-BLOCK PARSERS — @field / @option (one-liner), @body / @on_submit (block)
# ─────────────────────────────────────────────────────────────

def _make_oneliner_parser(plugin_name: str):
    """Parse bodyless one-liner sub-commands like @field[...] / @option[...]."""
    def _p(parser):
        from cruhon.core.ast_nodes import PluginBlockNode
        line = parser.current.line
        parser.advance()  # @field / @option
        args, kwargs = parser.parse_named_args()
        return PluginBlockNode(plugin_name=plugin_name, args=args,
                               kwargs=kwargs, body=[], line=line)
    return _p


def _noop_visit(transpiler, node):
    """field/option rendered standalone (normally handled by parent)."""
    return f"{'    ' * transpiler._indent}pass"


_TEXT_STYLES = {"short": "short", "long": "long", "paragraph": "paragraph"}


def _render_field(field_node) -> str:
    """@field[Title; placeholder=..; max=..; style=long] → TextInput attribute."""
    args = field_node.args
    kw = field_node.kwargs
    label = _as_str(args[0]) if args else '"Field"'
    attr = _slug(args[0] if args else 'field')
    parts = [f"label={label}"]
    if "placeholder" in kw:
        parts.append(f"placeholder={kw['placeholder'].strip()}")
    if "style" in kw:
        st = kw["style"].strip().strip("\"'").lower()
        parts.append(f"style=discord.TextStyle.{_TEXT_STYLES.get(st, st)}")
    if "required" in kw:
        parts.append(f"required={kw['required'].strip()}")
    if "max" in kw:
        parts.append(f"max_length={kw['max'].strip()}")
    if "min" in kw:
        parts.append(f"min_length={kw['min'].strip()}")
    if "default" in kw:
        parts.append(f"default={kw['default'].strip()}")
    return f"{attr} = discord.ui.TextInput({', '.join(parts)})"


def _render_option(opt_node) -> str:
    """@option[Red; value=red; emoji=🔴] → discord.SelectOption(...)."""
    args = opt_node.args
    kw = opt_node.kwargs
    label = _as_str(args[0]) if args else '"Option"'
    parts = [f"label={label}"]
    if "value" in kw:
        v = kw["value"].strip()
        # unquoted value like value=red → make it a string
        if not (v.startswith('"') or v.startswith("'")):
            v = repr(v.strip("\"'"))
        parts.append(f"value={v}")
    if "description" in kw:
        parts.append(f"description={kw['description'].strip()}")
    if "emoji" in kw:
        parts.append(f"emoji={kw['emoji'].strip()}")
    if "default" in kw:
        parts.append(f"default={kw['default'].strip()}")
    return f"discord.SelectOption({', '.join(parts)})"


# ─────────────────────────────────────────────────────────────
# MODAL BLOCK VISITOR — form/modal window
# ─────────────────────────────────────────────────────────────

def _visit_dc_modal(transpiler, node):
    """
    @discord.modal[Feedback; FeedbackModal]
        @field[Subject; placeholder="Topic"]
        @on_submit[interaction] ... @end
    @end
    → class FeedbackModal(discord.ui.Modal, title="Feedback"): ...
    """
    from cruhon.core.ast_nodes import PluginBlockNode

    title = _as_str(node.args[0]) if node.args else '"Form"'
    cls = (node.args[1].strip().strip("\"'")) if len(node.args) > 1 else "MyModal"

    base = "    " * transpiler._indent
    lines = [f"{base}class {cls}(discord.ui.Modal, title={title}):"]

    transpiler._indent += 1
    inner = "    " * transpiler._indent
    submit_node = None
    field_count = 0
    try:
        for child in node.body:
            if isinstance(child, PluginBlockNode) and child.plugin_name == "_dc_field":
                lines.append(f"{inner}{_render_field(child)}")
                field_count += 1
            elif isinstance(child, PluginBlockNode) and child.plugin_name == "on_submit":
                submit_node = child

        # on_submit method
        if submit_node is not None:
            ctx = submit_node.args[0].strip() if submit_node.args else "interaction"
            body_code = transpiler._block(submit_node.body)
            lines.append(f"{inner}async def on_submit(self, {ctx}):")
            lines.append(body_code if body_code.strip() else f"{inner}    pass")
        if field_count == 0 and submit_node is None:
            lines.append(f"{inner}pass")
    finally:
        transpiler._indent -= 1

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# SELECT — all 5 discord.py select types
# ─────────────────────────────────────────────────────────────

# plugin_name → discord.ui decorator name
_SELECT_TYPES = {
    "_dc_select":              "select",
    "_dc_user_select":         "user_select",
    "_dc_role_select":         "role_select",
    "_dc_channel_select":      "channel_select",
    "_dc_mentionable_select":  "mentionable_select",
}
_ALL_SELECT_NAMES = set(_SELECT_TYPES)


def _render_any_select(transpiler, node):
    """
    Unified renderer for all discord.py select types.

    String select (@discord.select):
      @discord.select[Choose; min=1; max=1]
          @option[Red; value=red]
          @body[interaction; selection]
              @discord.respond[interaction; selection[0]]
          @end
      @end

    Typed selects (user / role / channel / mentionable):
      @discord.user_select[Pick a user; min=1; max=1]
          @body[interaction; selection]
              @discord.respond[interaction; selection[0].mention]
          @end
      @end

    Channel select additionally accepts channel_types kwarg:
      @discord.channel_select[Pick; channel_types=text,voice]
    """
    from cruhon.core.ast_nodes import PluginBlockNode

    select_type = _SELECT_TYPES.get(node.plugin_name, "select")
    placeholder = _as_str(node.args[0]) if node.args else '"Select"'
    kw = node.kwargs
    name = _slug(node.args[0] if node.args else 'select')

    deco = [f"placeholder={placeholder}"]
    if "min" in kw:
        deco.append(f"min_values={kw['min'].strip()}")
    if "max" in kw:
        deco.append(f"max_values={kw['max'].strip()}")
    if "channel_types" in kw:
        raw = kw["channel_types"].strip().strip("[]")
        types = ", ".join(f"discord.ChannelType.{t.strip()}" for t in raw.split(",") if t.strip())
        deco.append(f"channel_types=[{types}]")

    # Options are only relevant for string select
    options = []
    body_node = None
    for child in node.body:
        if isinstance(child, PluginBlockNode) and child.plugin_name == "_dc_option":
            options.append(_render_option(child))
        elif isinstance(child, PluginBlockNode) and child.plugin_name == "body":
            body_node = child
    if options:
        deco.append(f"options=[{', '.join(options)}]")

    if body_node is not None:
        ctx = body_node.args[0].strip() if body_node.args else "interaction"
        sel = body_node.args[1].strip() if len(body_node.args) > 1 else "select"
        body_src = body_node.body
    else:
        ctx, sel, body_src = "interaction", "select", []

    base = "    " * transpiler._indent
    saved = transpiler._indent
    transpiler._indent += 1
    inner_body = "\n".join(filter(None, (n.accept(transpiler) for n in body_src)))
    transpiler._indent = saved

    return "\n".join([
        f"{base}@discord.ui.{select_type}({', '.join(deco)})",
        f"{base}async def {name}(self, {ctx}, {sel}):",
        inner_body if inner_body.strip() else f"{base}    pass",
    ])


def _render_select(transpiler, node):
    """Legacy alias → _render_any_select."""
    return _render_any_select(transpiler, node)


def _visit_dc_select(transpiler, node):
    return _render_any_select(transpiler, node)

def _visit_dc_user_select(transpiler, node):
    return _render_any_select(transpiler, node)

def _visit_dc_role_select(transpiler, node):
    return _render_any_select(transpiler, node)

def _visit_dc_channel_select(transpiler, node):
    return _render_any_select(transpiler, node)

def _visit_dc_mentionable_select(transpiler, node):
    return _render_any_select(transpiler, node)


# ─────────────────────────────────────────────────────────────
# @embed / @discord.quick_embed — one-liner full embed
# ─────────────────────────────────────────────────────────────

# Positional arg order: title description color footer image thumbnail author
_EMBED_POSITIONS = ("title", "description", "color", "footer", "image", "thumbnail", "author")


def _embed_code(args: list) -> str:
    """
    Shared code generator — used by both @embed[...] and @discord.quick_embed[...].

    Supported forms:
      Positional:   @embed["T"; "D"; 0xFF; "footer"; "img"; "thumb"; "author"]
      Kwargs:       @embed["T"; "D"; color=0xFF; footer="f"; author="a"]
      Mixed:        @embed["T"; "D"; footer="f"]   (remaining positions skipped)

    Empty string ("" or '') → that field is omitted.
    Generated Python:  __embed__(title=..., description=..., ...)
    __embed__ is a runtime helper injected via api.inject().
    """
    positional = []
    kwargs: dict[str, str] = {}

    for a in args:
        a = a.strip()
        # detect kwargs: identifier = value
        eq = a.find("=")
        if eq > 0 and a[:eq].strip().replace("_", "").isalpha():
            k = a[:eq].strip()
            v = a[eq + 1:].strip()
            kwargs[k] = v
        else:
            positional.append(a)

    # Map positional args to dict (skipped when kwargs are present)
    for i, val in enumerate(positional):
        if i >= len(_EMBED_POSITIONS):
            break
        field = _EMBED_POSITIONS[i]
        if field not in kwargs:
            kwargs[field] = val

    # Drop empty string values: "" or ''
    kwargs = {k: v for k, v in kwargs.items() if v not in ('""', "''", "")}

    if not kwargs:
        return "__embed__()"

    # "color"/"colour" stay raw expressions (ints, hex literals, @discord.color[...]
    # results) — everything else is display text and gets f-string upgrading /
    # variable-reference detection via _as_str().
    _RAW_FIELDS = ("color", "colour")
    parts = [
        f"{k}={v if k in _RAW_FIELDS else _as_str(v)}"
        for k, v in kwargs.items()
    ]
    return f"__embed__({', '.join(parts)})"


def _cruhon_color_helper(v):
    """
    Runtime helper — injected as __discord_color__ via api.inject().

    Handles @discord.color[some_variable] where the variable's actual
    runtime value could be a hex string ("#3498db"), an int, a named
    color string ("red"), or already a discord.Color — the transpiler
    can't know which at compile time, so this defers the decision to
    runtime, the same way @discord.color["#3498db"]/@discord.color[red]
    (both known at compile time) are already handled directly in the
    color() handler below.
    """
    import discord as _discord

    if isinstance(v, _discord.Color):
        return v
    if isinstance(v, int):
        return _discord.Color(v)
    if isinstance(v, str):
        s = v.strip().strip("\"'")
        if s.startswith("#"):
            return _discord.Color(int(s[1:], 16))
        if s.lower().startswith("0x"):
            return _discord.Color(int(s, 16))
        method = getattr(_discord.Color, s, None)
        if callable(method):
            return method()
        return _discord.Color(int(s))
    return _discord.Color.default()


def _cruhon_embed_helper(**kwargs):
    """
    Runtime helper — injected as __embed__ via api.inject().
    Transpilation works without discord installed; embed creation happens at runtime.
    """
    import discord as _discord

    # Color
    color = kwargs.get("color") or kwargs.get("colour")

    e = _discord.Embed(
        title=str(kwargs["title"]) if kwargs.get("title") else "",
        description=str(kwargs["description"]) if kwargs.get("description") else "",
        color=color,
    )

    # Footer
    if kwargs.get("footer"):
        icon = kwargs.get("footer_icon") or kwargs.get("footer_icon_url")
        if icon:
            e.set_footer(text=str(kwargs["footer"]), icon_url=str(icon))
        else:
            e.set_footer(text=str(kwargs["footer"]))

    # Image / Thumbnail
    if kwargs.get("image"):
        e.set_image(url=str(kwargs["image"]))
    if kwargs.get("thumbnail"):
        e.set_thumbnail(url=str(kwargs["thumbnail"]))

    # Author
    if kwargs.get("author"):
        icon = kwargs.get("author_icon") or kwargs.get("author_icon_url")
        if icon:
            e.set_author(name=str(kwargs["author"]), icon_url=str(icon))
        else:
            e.set_author(name=str(kwargs["author"]))

    # URL
    if kwargs.get("url"):
        e.url = str(kwargs["url"])

    return e


async def _cruhon_paginate(dest, pages, timeout=180):
    """Multi-page embed navigator with ⬅️ ➡️ ⏹️ buttons.
    Injected as __paginate__ via api.inject."""
    import discord
    pages = list(pages)
    if not pages:
        return
    st = {"i": 0}

    def _emb(p):
        return p if isinstance(p, discord.Embed) else discord.Embed(description=str(p))

    view = discord.ui.View(timeout=timeout)
    prev = discord.ui.Button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    nxt = discord.ui.Button(emoji="➡️", style=discord.ButtonStyle.secondary)
    stop_b = discord.ui.Button(emoji="⏹️", style=discord.ButtonStyle.danger)

    async def _go(interaction):
        await interaction.response.edit_message(embed=_emb(pages[st["i"]]), view=view)

    async def _prev(interaction):
        st["i"] = (st["i"] - 1) % len(pages); await _go(interaction)

    async def _next(interaction):
        st["i"] = (st["i"] + 1) % len(pages); await _go(interaction)

    async def _stop(interaction):
        await interaction.response.edit_message(view=None); view.stop()

    prev.callback, nxt.callback, stop_b.callback = _prev, _next, _stop
    view.add_item(prev); view.add_item(nxt); view.add_item(stop_b)

    first = _emb(pages[0])
    if hasattr(dest, "response") and hasattr(dest.response, "send_message"):
        await dest.response.send_message(embed=first, view=view)
    else:
        await dest.send(embed=first, view=view)


async def _cruhon_confirm(dest, text="Are you sure?", timeout=60):
    """Yes/No confirmation dialog — returns bool.
    Injected as __confirm__ via api.inject."""
    import discord, asyncio
    res = {"v": None}
    view = discord.ui.View(timeout=timeout)
    yes = discord.ui.Button(label="Yes", style=discord.ButtonStyle.success)
    no = discord.ui.Button(label="No", style=discord.ButtonStyle.danger)
    done = asyncio.Event()

    async def _yes(i):
        res["v"] = True; await i.response.edit_message(content="✅", view=None); done.set()

    async def _no(i):
        res["v"] = False; await i.response.edit_message(content="❌", view=None); done.set()

    yes.callback, no.callback = _yes, _no
    view.add_item(yes); view.add_item(no)

    if hasattr(dest, "response") and hasattr(dest.response, "send_message"):
        await dest.response.send_message(text, view=view)
    else:
        await dest.send(text, view=view)

    try:
        await asyncio.wait_for(done.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        pass
    return res["v"]


def _cruhon_progress(value, total, length=10, filled="▰", empty="▱"):
    """Text progress bar — injected as __progress__ via api.inject.
    __progress__(7, 10) → '▰▰▰▰▰▰▰▱▱▱'"""
    try:
        ratio = float(value) / float(total) if total else 0.0
    except (TypeError, ZeroDivisionError):
        ratio = 0.0
    n = int(round(length * max(0.0, min(1.0, ratio))))
    return filled * n + empty * (length - n)


def _embed_inline_handler(parser):
    """
    Handler for api.inline_command("embed").
    Triggered when @embed[...] is used inline (e.g. @var[e; @embed["T";"D"]]).
    """
    parser.advance()  # consume @embed token
    args = parser.parse_args()
    return _embed_code(args)


# ─────────────────────────────────────────────────────────────
# LIB_CALL HANDLERS — all non-block @discord.X[...] commands
# ─────────────────────────────────────────────────────────────

def _build_handlers() -> dict:
    """
    Returns {method_name: handler(args) -> str} for all
    inline/statement-level discord commands.
    handler(args) returns a Python expression or statement string.
    """
    h = {}

    # ── NESTED PASSTHROUGH (full discord.py freedom) ──────────
    # Produced by the lexer hook for @discord.a.b.c[...] forms.
    # args[0] = "discord.ui.Button" (string literal, with quotes)
    # rest    = the real call arguments → discord.ui.Button(rest...)
    def __nested(args):
        if not args:
            return "discord"
        path = args[0].strip().strip("\"'")
        rest = [a for a in args[1:]]
        return f"{path}({', '.join(rest)})"
    h["__nested"] = __nested

    # ── BOT SETUP ─────────────────────────────────────────────

    def setup(args):
        token = args[0] if args else '""'
        prefix = '"!"'
        intents_name = "default"
        for a in args[1:]:
            a = a.strip()
            if a.startswith("prefix="):
                # _as_str: quoted literal ("?") stays a literal, {braces}
                # upgrade to an f-string, and a bare variable name (the
                # overwhelmingly likely case when prefix comes from
                # @env.get[...]) passes through as a real reference
                # instead of being coerced into the literal text "prefix".
                prefix = _as_str(a[7:].strip())
            elif a.startswith("intents="):
                intents_name = a[8:].strip().strip("\"'")
        if intents_name == "all":
            intents = "discord.Intents.all()"
        elif intents_name == "none":
            intents = "discord.Intents.none()"
        else:
            intents = "discord.Intents.default()"
        return (
            f"import discord\n"
            f"import asyncio\n"
            f"from discord.ext import commands\n"
            f"from discord.ext import tasks as __discord_tasks__\n"
            f"__discord_token__ = {token}\n"
            f"__bot__ = commands.Bot(command_prefix={prefix}, intents={intents})"
        )
    h["setup"] = setup

    def run(args):
        return "__bot__.run(__discord_token__)"
    h["run"] = run

    def sync_commands(args):
        return "await __bot__.tree.sync()"
    h["sync_commands"] = sync_commands

    def add_cog(args):
        # @discord.add_cog[Moderation] — use in async context (on_ready/setup)
        name = args[0].strip() if args else "MyCog"
        return f"await __bot__.add_cog({name}(__bot__))"
    h["add_cog"] = add_cog

    def add_view(args):
        # @discord.add_view[ConfirmView] — register a persistent view
        name = args[0].strip() if args else "MyView"
        return f"__bot__.add_view({name}())"
    h["add_view"] = add_view

    def start_task(args):
        name = args[0] if args else "background_task"
        return f"{name}.start()"
    h["start_task"] = start_task

    def stop_task(args):
        name = args[0] if args else "background_task"
        return f"{name}.stop()"
    h["stop_task"] = stop_task

    # ── MESSAGING ─────────────────────────────────────────────

    def send(args):
        if not args:
            return 'await ctx.send("")'
        channel = args[0]
        if len(args) == 1:
            return f"await {channel}.send()"
        # Collect kwargs from remaining args
        extra_kw = [a.strip() for a in args[2:] if "=" in a.strip()]
        raw_text = args[1]
        # If text is a kwarg (e.g. embed=x), shift
        if "=" in raw_text.strip() and raw_text.strip().split("=")[0].isidentifier():
            kw_str = ", ".join([raw_text.strip()] + extra_kw)
            return f"await {channel}.send({kw_str})"
        text = _as_str(raw_text)
        if extra_kw:
            kw_str = ", ".join(extra_kw)
            return f"await {channel}.send({text}, {kw_str})"
        return f"await {channel}.send({text})"
    h["send"] = send

    def send_embed(args):
        channel = args[0] if args else "channel"
        embed = args[1] if len(args) > 1 else "embed"
        return f"await {channel}.send(embed={embed})"
    h["send_embed"] = send_embed

    def reply(args):
        target = args[0] if args else "ctx"
        text = _as_str(args[1]) if len(args) > 1 else '""'
        extra_kw = [a.strip() for a in args[2:] if "=" in a.strip()]
        if extra_kw:
            return f"await {target}.reply({text}, {', '.join(extra_kw)})"
        return f"await {target}.reply({text})"
    h["reply"] = reply

    def dm(args):
        user = args[0] if args else "user"
        text = _as_str(args[1]) if len(args) > 1 else '""'
        return f"await {user}.send({text})"
    h["dm"] = dm

    def respond(args):
        interaction = args[0] if args else "interaction"
        text = _as_str(args[1]) if len(args) > 1 else '""'
        extra_kw = [a.strip() for a in args[2:] if "=" in a.strip()]
        if extra_kw:
            return f"await {interaction}.response.send_message({text}, {', '.join(extra_kw)})"
        return f"await {interaction}.response.send_message({text})"
    h["respond"] = respond

    def respond_embed(args):
        interaction = args[0] if args else "interaction"
        embed = args[1] if len(args) > 1 else "embed"
        ephemeral = any(a.strip() == "ephemeral=True" for a in args[2:])
        if ephemeral:
            return f"await {interaction}.response.send_message(embed={embed}, ephemeral=True)"
        return f"await {interaction}.response.send_message(embed={embed})"
    h["respond_embed"] = respond_embed

    def defer(args):
        interaction = args[0] if args else "interaction"
        ephemeral = len(args) > 1 and args[1].strip() in ("True", "ephemeral=True")
        if ephemeral:
            return f"await {interaction}.response.defer(ephemeral=True)"
        return f"await {interaction}.response.defer()"
    h["defer"] = defer

    def followup(args):
        interaction = args[0] if args else "interaction"
        text = _as_str(args[1]) if len(args) > 1 else '""'
        extra_kw = [a.strip() for a in args[2:] if "=" in a.strip()]
        if extra_kw:
            return f"await {interaction}.followup.send({text}, {', '.join(extra_kw)})"
        return f"await {interaction}.followup.send({text})"
    h["followup"] = followup

    def edit(args):
        message = args[0] if args else "message"
        content = _as_str(args[1]) if len(args) > 1 else '""'
        return f"await {message}.edit(content={content})"
    h["edit"] = edit

    def edit_embed(args):
        message = args[0] if args else "message"
        embed = args[1] if len(args) > 1 else "embed"
        return f"await {message}.edit(embed={embed})"
    h["edit_embed"] = edit_embed

    def dm_embed(args):
        user = args[0] if args else "user"
        embed = args[1] if len(args) > 1 else "embed"
        return f"await {user}.send(embed={embed})"
    h["dm_embed"] = dm_embed

    def send_modal(args):
        # @discord.send_modal[interaction; FeedbackModal]
        interaction = args[0] if args else "interaction"
        modal = args[1].strip() if len(args) > 1 else "MyModal"
        # Allow passing an instance (Modal(...)) or a class name (→ instantiate)
        inst = modal if modal.endswith(")") else f"{modal}()"
        return f"await {interaction}.response.send_modal({inst})"
    h["send_modal"] = send_modal

    def delete(args):
        message = args[0] if args else "message"
        for a in args[1:]:
            if a.strip().startswith("delay="):
                return f"await {message}.delete(delay={a.strip()[6:]})"
        return f"await {message}.delete()"
    h["delete"] = delete

    def pin(args):
        return f"await {args[0] if args else 'message'}.pin()"
    h["pin"] = pin

    def unpin(args):
        return f"await {args[0] if args else 'message'}.unpin()"
    h["unpin"] = unpin

    def process_commands(args):
        msg = args[0] if args else "message"
        return f"await __bot__.process_commands({msg})"
    h["process_commands"] = process_commands

    # ── REACTIONS ─────────────────────────────────────────────

    def react(args):
        message = args[0] if args else "message"
        emoji = args[1] if len(args) > 1 else '"👍"'
        return f"await {message}.add_reaction({emoji})"
    h["react"] = react

    def unreact(args):
        message = args[0] if args else "message"
        emoji = args[1] if len(args) > 1 else '"👍"'
        user = args[2] if len(args) > 2 else "__bot__.user"
        return f"await {message}.remove_reaction({emoji}, {user})"
    h["unreact"] = unreact

    def add_reactions(args):
        # @discord.add_reactions[msg; "👍"; "👎"; "❤️"] → add several reactions in order
        message = args[0] if args else "message"
        emojis = [a.strip() for a in args[1:] if "=" not in a.strip()]
        if not emojis:
            return f'await {message}.add_reaction("👍")'
        return f"[await {message}.add_reaction(__e) for __e in [{', '.join(emojis)}]]"
    h["add_reactions"] = add_reactions

    def clear_reactions(args):
        return f"await {args[0] if args else 'message'}.clear_reactions()"
    h["clear_reactions"] = clear_reactions

    # ── EMBED ──────────────────────────────────────────────────

    def quick_embed(args):
        """@discord.quick_embed[...] — same as @embed, with @discord. prefix."""
        return _embed_code(args)
    h["quick_embed"] = quick_embed

    def embed(args):
        title = _as_str(args[0]) if args else '""'
        description = _as_str(args[1]) if len(args) > 1 else '""'
        color_val = None
        for a in args[2:]:
            a = a.strip()
            if a.startswith("color=") or a.startswith("colour="):
                color_val = a.split("=", 1)[1]
        if color_val:
            return f"discord.Embed(title={title}, description={description}, color={color_val})"
        return f"discord.Embed(title={title}, description={description})"
    h["embed"] = embed

    def add_field(args):
        emb = args[0] if args else "embed"
        name = _as_str(args[1]) if len(args) > 1 else '""'
        value = _as_str(args[2]) if len(args) > 2 else '""'
        inline = True
        for a in args[3:]:
            if a.strip() == "inline=False":
                inline = False
        return f"{emb}.add_field(name={name}, value={value}, inline={inline})"
    h["add_field"] = add_field

    def set_footer(args):
        emb = args[0] if args else "embed"
        text = _as_str(args[1]) if len(args) > 1 else '""'
        for a in args[2:]:
            if a.strip().startswith("icon="):
                return f"{emb}.set_footer(text={text}, icon_url={_as_str(a.strip()[5:])})"
        return f"{emb}.set_footer(text={text})"
    h["set_footer"] = set_footer

    def set_image(args):
        emb = args[0] if args else "embed"
        url = _as_str(args[1]) if len(args) > 1 else '""'
        return f"{emb}.set_image(url={url})"
    h["set_image"] = set_image

    def set_thumbnail(args):
        emb = args[0] if args else "embed"
        url = _as_str(args[1]) if len(args) > 1 else '""'
        return f"{emb}.set_thumbnail(url={url})"
    h["set_thumbnail"] = set_thumbnail

    def set_author(args):
        emb = args[0] if args else "embed"
        name = _as_str(args[1]) if len(args) > 1 else '""'
        for a in args[2:]:
            if a.strip().startswith("icon="):
                return f"{emb}.set_author(name={name}, icon_url={_as_str(a.strip()[5:])})"
        return f"{emb}.set_author(name={name})"
    h["set_author"] = set_author

    # ── MODERATION ────────────────────────────────────────────

    def ban(args):
        member = args[0] if args else "member"
        kw_parts = []
        for a in args[1:]:
            a = a.strip()
            if a.startswith("reason="):
                kw_parts.append(f"reason={_as_str(a[7:])}")
            elif a.startswith("delete_days="):
                kw_parts.append(f"delete_message_days={a[12:]}")
        kw = (", " + ", ".join(kw_parts)) if kw_parts else ""
        return f"await {member}.ban({kw.lstrip(', ')})"
    h["ban"] = ban

    def unban(args):
        guild = args[0] if args else "guild"
        user = args[1] if len(args) > 1 else "user"
        for a in args[2:]:
            if a.strip().startswith("reason="):
                return f"await {guild}.unban({user}, reason={_as_str(a.strip()[7:])})"
        return f"await {guild}.unban({user})"
    h["unban"] = unban

    def kick(args):
        member = args[0] if args else "member"
        for a in args[1:]:
            if a.strip().startswith("reason="):
                return f"await {member}.kick(reason={_as_str(a.strip()[7:])})"
        return f"await {member}.kick()"
    h["kick"] = kick

    def timeout(args):
        member = args[0] if args else "member"
        dt = "__import__('datetime').timedelta"
        for a in args[1:]:
            a = a.strip()
            if a.startswith("minutes="):
                return f"await {member}.timeout({dt}(minutes={a[8:]}))"
            if a.startswith("seconds="):
                return f"await {member}.timeout({dt}(seconds={a[8:]}))"
            if a.startswith("hours="):
                return f"await {member}.timeout({dt}(hours={a[6:]}))"
            if not "=" in a:
                return f"await {member}.timeout({dt}(minutes={a}))"
        return f"await {member}.timeout({dt}(minutes=10))"
    h["timeout"] = timeout

    def untimeout(args):
        return f"await {args[0] if args else 'member'}.timeout(None)"
    h["untimeout"] = untimeout

    def add_role(args):
        member = args[0] if args else "member"
        role = args[1] if len(args) > 1 else "role"
        return f"await {member}.add_roles({role})"
    h["add_role"] = add_role

    def remove_role(args):
        member = args[0] if args else "member"
        role = args[1] if len(args) > 1 else "role"
        return f"await {member}.remove_roles({role})"
    h["remove_role"] = remove_role

    def nickname(args):
        member = args[0] if args else "member"
        nick = _as_str(args[1]) if len(args) > 1 else '""'
        return f"await {member}.edit(nick={nick})"
    h["nickname"] = nickname

    # ── CHANNELS ──────────────────────────────────────────────

    def purge(args):
        channel = args[0] if args else "channel"
        limit = args[1] if len(args) > 1 else "10"
        return f"await {channel}.purge(limit={limit})"
    h["purge"] = purge

    def create_text(args):
        guild = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '"new-channel"'
        for a in args[2:]:
            if a.strip().startswith("category="):
                return f"await {guild}.create_text_channel({name}, category={a.strip()[9:]})"
        return f"await {guild}.create_text_channel({name})"
    h["create_text"] = create_text

    def create_voice(args):
        guild = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '"new-voice"'
        return f"await {guild}.create_voice_channel({name})"
    h["create_voice"] = create_voice

    def delete_channel(args):
        return f"await {args[0] if args else 'channel'}.delete()"
    h["delete_channel"] = delete_channel

    # ── LOOKUP (returns as expression) ────────────────────────

    def get_member(args):
        guild = args[0] if args else "guild"
        id_ = args[1] if len(args) > 1 else "0"
        return f"{guild}.get_member({id_})"
    h["get_member"] = get_member

    def get_channel(args):
        guild = args[0] if args else "guild"
        id_ = args[1] if len(args) > 1 else "0"
        return f"{guild}.get_channel({id_})"
    h["get_channel"] = get_channel

    def get_role(args):
        guild = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '""'
        return f"discord.utils.get({guild}.roles, name={name})"
    h["get_role"] = get_role

    def find_member(args):
        guild = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '""'
        return f"discord.utils.find(lambda __m__: __m__.name == {name}, {guild}.members)"
    h["find_member"] = find_member

    def me(args):
        return "__bot__.user"
    h["me"] = me

    def mention(args):
        return f"{args[0] if args else 'member'}.mention"
    h["mention"] = mention

    # ── PROTECTION ────────────────────────────────────────────

    def ignore_self(args):
        msg = args[0] if args else "message"
        return f"if {msg}.author == __bot__.user: return"
    h["ignore_self"] = ignore_self

    def ignore_bots(args):
        msg = args[0] if args else "message"
        return f"if {msg}.author.bot: return"
    h["ignore_bots"] = ignore_bots

    def require_role(args):
        ctx = args[0] if args else "ctx"
        role = _as_str(args[1]) if len(args) > 1 else '"member"'
        err = _as_str(args[2]) if len(args) > 2 else '"You do not have permission to use this command."'
        return (
            f"if not discord.utils.get({ctx}.author.roles, name={role}): "
            f"await {ctx}.send({err}); return"
        )
    h["require_role"] = require_role

    def require_guild(args):
        ctx = args[0] if args else "ctx"
        return (
            f'if {ctx}.guild is None: '
            f'await {ctx}.send("This command can only be used in servers."); return'
        )
    h["require_guild"] = require_guild

    # ── STATUS & MISC ──────────────────────────────────────────

    def status(args):
        text = _as_str(args[0]) if args else '""'
        activity_type = "game"
        for a in args[1:]:
            if a.strip().startswith("type="):
                activity_type = a.strip()[5:].strip("\"'").lower()
        if activity_type == "watching":
            return (
                f"await __bot__.change_presence("
                f"activity=discord.Activity(type=discord.ActivityType.watching, name={text}))"
            )
        if activity_type == "listening":
            return (
                f"await __bot__.change_presence("
                f"activity=discord.Activity(type=discord.ActivityType.listening, name={text}))"
            )
        if activity_type == "streaming":
            url = _as_str(args[2]) if len(args) > 2 else '""'
            return (
                f"await __bot__.change_presence("
                f"activity=discord.Streaming(name={text}, url={url}))"
            )
        return f"await __bot__.change_presence(activity=discord.Game(name={text}))"
    h["status"] = status

    def log(args):
        text = _as_str(args[0]) if args else '""'
        return f'print("[bot]", {text})'
    h["log"] = log

    def wait_for(args):
        event = args[0] if args else '"message"'
        kw_parts = []
        for a in args[1:]:
            a = a.strip()
            if a.startswith("timeout=") or a.startswith("check="):
                kw_parts.append(a)
        if kw_parts:
            return f"await __bot__.wait_for({event}, {', '.join(kw_parts)})"
        return f"await __bot__.wait_for({event})"
    h["wait_for"] = wait_for

    # ── VOICE ─────────────────────────────────────────────────

    def join(args):
        channel = args[0] if args else "voice_channel"
        return f"await {channel}.connect()"
    h["join"] = join

    def leave(args):
        guild = args[0] if args else "guild"
        return f"await {guild}.voice_client.disconnect()"
    h["leave"] = leave

    # ── SHORTCUTS ─────────────────────────────────────────────
    # Helper: forward positional + kwargs individually
    def _kw(args, start=0):
        return [a.strip() for a in args[start:] if "=" in a.strip()
                and a.strip().split("=")[0].strip().isidentifier()]

    def _call(target, method, pos, args, kw_start):
        parts = list(pos) + _kw(args, kw_start)
        return f"await {target}.{method}({', '.join(parts)})"

    # ── FETCH (API calls — from server instead of cache) ──────
    def fetch_user(args):
        return f"await __bot__.fetch_user({args[0] if args else '0'})"
    h["fetch_user"] = fetch_user

    def fetch_channel(args):
        return f"await __bot__.fetch_channel({args[0] if args else '0'})"
    h["fetch_channel"] = fetch_channel

    def fetch_guild(args):
        return f"await __bot__.fetch_guild({args[0] if args else '0'})"
    h["fetch_guild"] = fetch_guild

    def fetch_member(args):
        g = args[0] if args else "guild"
        i = args[1] if len(args) > 1 else "0"
        return f"await {g}.fetch_member({i})"
    h["fetch_member"] = fetch_member

    def fetch_message(args):
        ch = args[0] if args else "channel"
        i = args[1] if len(args) > 1 else "0"
        return f"await {ch}.fetch_message({i})"
    h["fetch_message"] = fetch_message

    def history(args):
        ch = args[0] if args else "channel"
        limit = args[1] if len(args) > 1 else "100"
        return f"[__m async for __m in {ch}.history(limit={limit})]"
    h["history"] = history

    # ── THREAD ────────────────────────────────────────────────
    def create_thread(args):
        ch = args[0] if args else "channel"
        name = _as_str(args[1]) if len(args) > 1 else '"thread"'
        return _call(ch, "create_thread", [f"name={name}"], args, 2)
    h["create_thread"] = create_thread

    def thread_from(args):
        msg = args[0] if args else "message"
        name = _as_str(args[1]) if len(args) > 1 else '"thread"'
        return f"await {msg}.create_thread(name={name})"
    h["thread_from"] = thread_from

    def join_thread(args):
        return f"await {args[0] if args else 'thread'}.join()"
    h["join_thread"] = join_thread

    def leave_thread(args):
        return f"await {args[0] if args else 'thread'}.leave()"
    h["leave_thread"] = leave_thread

    def archive_thread(args):
        return f"await {args[0] if args else 'thread'}.edit(archived=True)"
    h["archive_thread"] = archive_thread

    def add_thread_member(args):
        t = args[0] if args else "thread"
        m = args[1] if len(args) > 1 else "member"
        return f"await {t}.add_user({m})"
    h["add_thread_member"] = add_thread_member

    # ── WEBHOOK ───────────────────────────────────────────────
    def create_webhook(args):
        ch = args[0] if args else "channel"
        name = _as_str(args[1]) if len(args) > 1 else '"webhook"'
        return _call(ch, "create_webhook", [f"name={name}"], args, 2)
    h["create_webhook"] = create_webhook

    def send_webhook(args):
        wh = args[0] if args else "webhook"
        content = _as_str(args[1]) if len(args) > 1 else '""'
        return _call(wh, "send", [content], args, 2)
    h["send_webhook"] = send_webhook

    # ── INVITE ────────────────────────────────────────────────
    def create_invite(args):
        ch = args[0] if args else "channel"
        return _call(ch, "create_invite", [], args, 1)
    h["create_invite"] = create_invite

    def delete_invite(args):
        return f"await {args[0] if args else 'invite'}.delete()"
    h["delete_invite"] = delete_invite

    def fetch_invites(args):
        return f"await {args[0] if args else 'guild'}.invites()"
    h["fetch_invites"] = fetch_invites

    # ── POLL ──────────────────────────────────────────────────
    def create_poll(args):
        question = _as_str(args[0]) if args else '"Question"'
        # @discord.create_poll["Question?"; "A"; "B"; "C"]  → answers
        answers = [a.strip() for a in args[1:] if "=" not in a.strip()]
        ans_code = "; ".join(answers)
        lines = [f"discord.Poll(question={question}, duration=__import__('datetime').timedelta(hours=24))"]
        if answers:
            chain = f"discord.Poll(question={question}, duration=__import__('datetime').timedelta(hours=24))"
            return ("(lambda __p: ([__p.add_answer(text=__a) for __a in [" +
                    ", ".join(answers) + "]], __p)[1])(" + chain + ")")
        return lines[0]
    h["create_poll"] = create_poll

    def end_poll(args):
        return f"await {args[0] if args else 'message'}.end_poll()"
    h["end_poll"] = end_poll

    # ── SCHEDULED EVENT ───────────────────────────────────────
    def create_event(args):
        g = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '"Event"'
        return _call(g, "create_scheduled_event", [f"name={name}"], args, 2)
    h["create_event"] = create_event

    def cancel_event(args):
        return f"await {args[0] if args else 'event'}.cancel()"
    h["cancel_event"] = cancel_event

    # ── ROLE MANAGEMENT ───────────────────────────────────────
    def create_role(args):
        g = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '"role"'
        return _call(g, "create_role", [f"name={name}"], args, 2)
    h["create_role"] = create_role

    def delete_role(args):
        return f"await {args[0] if args else 'role'}.delete()"
    h["delete_role"] = delete_role

    def edit_role(args):
        return _call(args[0] if args else "role", "edit", [], args, 1)
    h["edit_role"] = edit_role

    # ── CATEGORY & CHANNEL ────────────────────────────────────
    def create_category(args):
        g = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '"Category"'
        return f"await {g}.create_category({name})"
    h["create_category"] = create_category

    def edit_channel(args):
        return _call(args[0] if args else "channel", "edit", [], args, 1)
    h["edit_channel"] = edit_channel

    def move_channel(args):
        ch = args[0] if args else "channel"
        pos = args[1] if len(args) > 1 else "0"
        return f"await {ch}.move(beginning=True) if {pos} == 0 else await {ch}.edit(position={pos})"
    h["move_channel"] = move_channel

    def set_permissions(args):
        ch = args[0] if args else "channel"
        target = args[1] if len(args) > 1 else "target"
        return _call(ch, "set_permissions", [target], args, 2)
    h["set_permissions"] = set_permissions

    def lock_channel(args):
        # @discord.lock_channel[channel]              — locks for @everyone
        # @discord.lock_channel[channel; role]        — locks for a specific role
        ch = args[0] if args else "channel"
        target = args[1] if len(args) > 1 else f"{ch}.guild.default_role"
        return f"await {ch}.set_permissions({target}, send_messages=False)"
    h["lock_channel"] = lock_channel

    def unlock_channel(args):
        ch = args[0] if args else "channel"
        target = args[1] if len(args) > 1 else f"{ch}.guild.default_role"
        return f"await {ch}.set_permissions({target}, send_messages=True)"
    h["unlock_channel"] = unlock_channel

    def set_slowmode(args):
        ch = args[0] if args else "channel"
        secs = args[1] if len(args) > 1 else "0"
        return f"await {ch}.edit(slowmode_delay={secs})"
    h["set_slowmode"] = set_slowmode

    # ── EMOJI & STICKER ───────────────────────────────────────
    def create_emoji(args):
        g = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '"emoji"'
        img = args[2] if len(args) > 2 else "b''"
        return f"await {g}.create_custom_emoji(name={name}, image={img})"
    h["create_emoji"] = create_emoji

    def delete_emoji(args):
        return f"await {args[0] if args else 'emoji'}.delete()"
    h["delete_emoji"] = delete_emoji

    # ── FILE SENDING ──────────────────────────────────────────
    def send_file(args):
        ch = args[0] if args else "channel"
        path = _as_str(args[1]) if len(args) > 1 else '"file.txt"'
        content = [args[2]] if len(args) > 2 and "=" not in args[2] else []
        parts = content + [f"file=discord.File({path})"]
        return f"await {ch}.send({', '.join(parts)})"
    h["send_file"] = send_file

    def send_files(args):
        ch = args[0] if args else "channel"
        paths = args[1] if len(args) > 1 else "[]"
        return f"await {ch}.send(files=[discord.File(__p) for __p in {paths}])"
    h["send_files"] = send_files

    # ── AUDIT LOG ─────────────────────────────────────────────
    def audit_logs(args):
        g = args[0] if args else "guild"
        limit = args[1] if len(args) > 1 else "100"
        return f"[__e async for __e in {g}.audit_logs(limit={limit})]"
    h["audit_logs"] = audit_logs

    # ── MEMBER ADVANCED ───────────────────────────────────────
    def move_to(args):
        m = args[0] if args else "member"
        ch = args[1] if len(args) > 1 else "channel"
        return f"await {m}.move_to({ch})"
    h["move_to"] = move_to

    def mute(args):
        return f"await {args[0] if args else 'member'}.edit(mute=True)"
    h["mute"] = mute

    def unmute(args):
        return f"await {args[0] if args else 'member'}.edit(mute=False)"
    h["unmute"] = unmute

    def deafen(args):
        return f"await {args[0] if args else 'member'}.edit(deafen=True)"
    h["deafen"] = deafen

    def undeafen(args):
        return f"await {args[0] if args else 'member'}.edit(deafen=False)"
    h["undeafen"] = undeafen

    def disconnect(args):
        return f"await {args[0] if args else 'member'}.move_to(None)"
    h["disconnect"] = disconnect

    # ── TYPING & GENERAL ──────────────────────────────────────
    def typing(args):
        return f"{args[0] if args else 'channel'}.typing()"
    h["typing"] = typing

    def send_typing(args):
        return f"await {args[0] if args else 'channel'}.typing()"
    h["send_typing"] = send_typing

    def crosspost(args):
        return f"await {args[0] if args else 'message'}.publish()"
    h["crosspost"] = crosspost

    def fetch_guilds(args):
        return "[__g async for __g in __bot__.fetch_guilds()]"
    h["fetch_guilds"] = fetch_guilds

    def latency(args):
        return "__bot__.latency"
    h["latency"] = latency

    def sync_tree(args):
        g = args[0] if args else None
        if g:
            return f"await __bot__.tree.sync(guild={g})"
        return "await __bot__.tree.sync()"
    h["sync_tree"] = sync_tree

    # ── WIDE COVERAGE ─────────────────────────────────────────

    # ── STAGE CHANNEL ─────────────────────────────────────────
    def create_stage(args):
        g = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '"Stage"'
        return f"await {g}.create_stage_channel({name})"
    h["create_stage"] = create_stage

    def start_stage(args):
        ch = args[0] if args else "channel"
        topic = _as_str(args[1]) if len(args) > 1 else '"Live"'
        return f"await {ch}.create_instance(topic={topic})"
    h["start_stage"] = start_stage

    def end_stage(args):
        ch = args[0] if args else "channel"
        return f"await {ch}.instance.delete() if {ch}.instance else None"
    h["end_stage"] = end_stage

    # ── FORUM ─────────────────────────────────────────────────
    def create_forum(args):
        g = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '"forum"'
        return f"await {g}.create_forum({name})"
    h["create_forum"] = create_forum

    def create_post(args):
        forum = args[0] if args else "forum"
        name = _as_str(args[1]) if len(args) > 1 else '"topic"'
        content = args[2] if len(args) > 2 else '""'
        return f"await {forum}.create_thread(name={name}, content={content})"
    h["create_post"] = create_post

    # ── BAN MANAGEMENT ────────────────────────────────────────
    def bulk_ban(args):
        g = args[0] if args else "guild"
        users = args[1] if len(args) > 1 else "[]"
        return f"await {g}.bulk_ban({users})"
    h["bulk_ban"] = bulk_ban

    def fetch_ban(args):
        g = args[0] if args else "guild"
        user = args[1] if len(args) > 1 else "user"
        return f"await {g}.fetch_ban({user})"
    h["fetch_ban"] = fetch_ban

    def fetch_bans(args):
        g = args[0] if args else "guild"
        return f"[__b async for __b in {g}.bans()]"
    h["fetch_bans"] = fetch_bans

    # ── GUILD OPERATIONS ──────────────────────────────────────
    def edit_guild(args):
        return _call(args[0] if args else "guild", "edit", [], args, 1)
    h["edit_guild"] = edit_guild

    def fetch_roles(args):
        return f"await {args[0] if args else 'guild'}.fetch_roles()"
    h["fetch_roles"] = fetch_roles

    def fetch_channels(args):
        return f"await {args[0] if args else 'guild'}.fetch_channels()"
    h["fetch_channels"] = fetch_channels

    def fetch_emojis(args):
        return f"await {args[0] if args else 'guild'}.fetch_emojis()"
    h["fetch_emojis"] = fetch_emojis

    def prune(args):
        g = args[0] if args else "guild"
        days = args[1] if len(args) > 1 else "30"
        return f"await {g}.prune_members(days={days})"
    h["prune"] = prune

    def leave_guild(args):
        return f"await {args[0] if args else 'guild'}.leave()"
    h["leave_guild"] = leave_guild

    # ── STICKER ───────────────────────────────────────────────
    def create_sticker(args):
        g = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '"sticker"'
        return _call(g, "create_sticker", [f"name={name}"], args, 2)
    h["create_sticker"] = create_sticker

    def delete_sticker(args):
        return f"await {args[0] if args else 'sticker'}.delete()"
    h["delete_sticker"] = delete_sticker

    # ── CHANNEL EXTRA ─────────────────────────────────────────
    def clone_channel(args):
        return f"await {args[0] if args else 'channel'}.clone()"
    h["clone_channel"] = clone_channel

    def fetch_pins(args):
        return f"await {args[0] if args else 'channel'}.pins()"
    h["fetch_pins"] = fetch_pins

    def clear_reaction(args):
        msg = args[0] if args else "message"
        emoji = args[1] if len(args) > 1 else '"👍"'
        return f"await {msg}.clear_reaction({emoji})"
    h["clear_reaction"] = clear_reaction

    # ── AUTOMOD (simple keyword filter shortcut) ──────────────
    def automod_keyword(args):
        g = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '"Filter"'
        keywords = args[2] if len(args) > 2 else "[]"
        return (
            f"await {g}.create_automod_rule(name={name}, "
            f"event_type=discord.AutoModRuleEventType.message_send, "
            f"trigger=discord.AutoModTrigger("
            f"type=discord.AutoModRuleTriggerType.keyword, keyword_filter={keywords}), "
            f"actions=[discord.AutoModRuleAction("
            f"type=discord.AutoModRuleActionType.block_message)])"
        )
    h["automod_keyword"] = automod_keyword

    def create_automod_rule(args):
        # @discord.create_automod_rule[guild; name=...; event_type=...; trigger=...; actions=...]
        # All config via kwargs — passes them directly to guild.create_automod_rule()
        g = args[0] if args else "guild"
        return _call(g, "create_automod_rule", [], args, 1)
    h["create_automod_rule"] = create_automod_rule

    def edit_automod_rule(args):
        # @discord.edit_automod_rule[rule; name=...; enabled=...; actions=...]
        rule = args[0] if args else "rule"
        return _call(rule, "edit", [], args, 1)
    h["edit_automod_rule"] = edit_automod_rule

    def delete_automod_rule(args):
        return f"await {args[0] if args else 'rule'}.delete()"
    h["delete_automod_rule"] = delete_automod_rule

    def fetch_automod_rules(args):
        g = args[0] if args else "guild"
        return f"await {g}.fetch_automod_rules()"
    h["fetch_automod_rules"] = fetch_automod_rules

    # ── MEMBER EXTRA ──────────────────────────────────────────
    def add_roles(args):
        m = args[0] if args else "member"
        roles = ", ".join(a.strip() for a in args[1:] if "=" not in a)
        return f"await {m}.add_roles({roles})"
    h["add_roles"] = add_roles

    def remove_roles(args):
        m = args[0] if args else "member"
        roles = ", ".join(a.strip() for a in args[1:] if "=" not in a)
        return f"await {m}.remove_roles({roles})"
    h["remove_roles"] = remove_roles

    def fetch_member_roles(args):
        return f"{args[0] if args else 'member'}.roles"
    h["member_roles"] = fetch_member_roles

    # ── POWER: PAGINATION & CONFIRM (runtime helpers) ─────────
    def paginate(args):
        dest = args[0] if args else "ctx"
        pages = args[1] if len(args) > 1 else "[]"
        for a in args[2:]:
            if a.strip().startswith("timeout="):
                return f"await __paginate__({dest}, {pages}, {a.strip()[8:]})"
        return f"await __paginate__({dest}, {pages})"
    h["paginate"] = paginate

    def confirm(args):
        dest = args[0] if args else "ctx"
        text = _as_str(args[1]) if len(args) > 1 else '"Are you sure?"'
        return f"await __confirm__({dest}, {text})"
    h["confirm"] = confirm

    # ── LOOKUP (cache-based, no await) ────────────────────────
    def get_guild(args):
        return f"__bot__.get_guild({args[0] if args else '0'})"
    h["get_guild"] = get_guild

    def get_user(args):
        return f"__bot__.get_user({args[0] if args else '0'})"
    h["get_user"] = get_user

    # ── MESSAGING EXTRAS ──────────────────────────────────────
    def send_tts(args):
        channel = args[0] if args else "channel"
        text = _as_str(args[1]) if len(args) > 1 else '""'
        return f"await {channel}.send({text}, tts=True)"
    h["send_tts"] = send_tts

    def respond_ephemeral(args):
        interaction = args[0] if args else "interaction"
        text = _as_str(args[1]) if len(args) > 1 else '""'
        extra_kw = [a.strip() for a in args[2:] if "=" in a.strip()]
        if extra_kw:
            return f"await {interaction}.response.send_message({text}, ephemeral=True, {', '.join(extra_kw)})"
        return f"await {interaction}.response.send_message({text}, ephemeral=True)"
    h["respond_ephemeral"] = respond_ephemeral

    def bulk_purge(args):
        channel = args[0] if args else "channel"
        messages = args[1] if len(args) > 1 else "[]"
        return f"await {channel}.delete_messages({messages})"
    h["bulk_purge"] = bulk_purge

    def fetch_webhook(args):
        url = args[0] if args else '""'
        return f"await discord.Webhook.from_url({url}, client=__bot__).fetch()"
    h["fetch_webhook"] = fetch_webhook

    # ── COLOR ─────────────────────────────────────────────────
    # discord.Color's real classmethod names — used to tell a genuine
    # named-color shortcut (@discord.color[red] → discord.Color.red())
    # apart from a bare VARIABLE reference that merely happens to also
    # be a valid identifier (@discord.color[hex_color], @discord.color[c]).
    # Only bare text matching one of these is treated as a named color;
    # anything else bare is a variable, routed through the __discord_color__
    # runtime helper, which resolves a hex string/int/named string/
    # already-a-Color value at runtime (unknowable at transpile time).
    _COLOR_NAMES = {
        "default", "random", "teal", "dark_teal", "green", "dark_green",
        "blue", "dark_blue", "purple", "dark_purple", "magenta",
        "dark_magenta", "gold", "dark_gold", "orange", "dark_orange",
        "red", "dark_red", "lighter_grey", "lighter_gray", "dark_grey",
        "dark_gray", "light_grey", "light_gray", "darker_grey",
        "darker_gray", "blurple", "greyple", "dark_theme", "fuchsia",
        "yellow", "dark_embed", "light_embed", "brand_green", "black",
        "white",
    }

    def color(args):
        # @discord.color["#3498db"]  →  discord.Color(3461339)
        # @discord.color[52; 152; 219]  →  discord.Color.from_rgb(52, 152, 219)
        # @discord.color[0x3498db]  →  discord.Color(0x3498db)
        # @discord.color[red]       →  discord.Color.red()   (named color)
        # @discord.color[my_var]    →  __discord_color__(my_var) (variable —
        #                               resolved to hex/int/name at runtime)
        if not args:
            return "discord.Color.default()"
        if len(args) >= 3:
            return f"discord.Color.from_rgb({args[0].strip()}, {args[1].strip()}, {args[2].strip()})"
        val = args[0].strip()
        is_quoted = val[:1] in ('"', "'")
        stripped = val.strip('"\'')
        if stripped.startswith('#'):
            try:
                num = int(stripped[1:], 16)
                return f"discord.Color({num})"
            except ValueError:
                pass
        if stripped in _COLOR_NAMES:
            return f"discord.Color.{stripped}()"
        if not is_quoted and _looks_like_expr(val):
            # A bare identifier/attribute chain that ISN'T a known color
            # name — a variable, not a literal. Defer to runtime.
            return f"__discord_color__({val})"
        return f"discord.Color({val})"
    h["color"] = color

    # ── VOICE AUDIO ───────────────────────────────────────────
    def play(args):
        # @discord.play[guild; "song.mp3"]
        # @discord.play[guild; source; volume=True]   → PCMVolumeTransformer
        guild = args[0] if args else "guild"
        source = args[1] if len(args) > 1 else '"audio.mp3"'
        for a in args[2:]:
            if a.strip() in ("volume=True", "transformer=True"):
                return (f"{guild}.voice_client.play("
                        f"discord.PCMVolumeTransformer(discord.FFmpegPCMAudio({source})))")
        return f"{guild}.voice_client.play(discord.FFmpegPCMAudio({source}))"
    h["play"] = play

    def stop_audio(args):
        guild = args[0] if args else "guild"
        return f"{guild}.voice_client.stop() if {guild}.voice_client else None"
    h["stop_audio"] = stop_audio

    def pause_audio(args):
        guild = args[0] if args else "guild"
        return f"{guild}.voice_client.pause() if {guild}.voice_client else None"
    h["pause_audio"] = pause_audio

    def resume_audio(args):
        guild = args[0] if args else "guild"
        return f"{guild}.voice_client.resume() if {guild}.voice_client else None"
    h["resume_audio"] = resume_audio

    def volume(args):
        # @discord.volume[guild; 0.5]  — requires PCMVolumeTransformer source
        guild = args[0] if args else "guild"
        vol = args[1] if len(args) > 1 else "0.5"
        return f"{guild}.voice_client.source.volume = {vol}"
    h["volume"] = volume

    def is_playing(args):
        guild = args[0] if args else "guild"
        return f"({guild}.voice_client is not None and {guild}.voice_client.is_playing())"
    h["is_playing"] = is_playing

    # ── INLINE CHECKS (boolean expressions) ───────────────────
    def has_role(args):
        # @if[@discord.has_role[member; "Admin"]]
        member = args[0] if args else "member"
        role = args[1] if len(args) > 1 else '"member"'
        return f"(discord.utils.get({member}.roles, name={role}) is not None)"
    h["has_role"] = has_role

    def has_perm(args):
        # @if[@discord.has_perm[member; ban_members]]
        member = args[0] if args else "member"
        perm = (args[1].strip().strip("\"'")) if len(args) > 1 else "administrator"
        return f"{member}.guild_permissions.{perm}"
    h["has_perm"] = has_perm

    def is_bot_owner(args):
        # @var[ok; await @discord.is_bot_owner[ctx.author]]  (coroutine)
        user = args[0] if args else "user"
        return f"await __bot__.is_owner({user})"
    h["is_bot_owner"] = is_bot_owner

    # ── FORMATTING & UTILS ────────────────────────────────────
    def timestamp(args):
        # @discord.timestamp[dt]       → <t:...:f>
        # @discord.timestamp[dt; "R"]  → <t:...:R> (relative: "3 minutes ago")
        dt = args[0] if args else "dt"
        if len(args) > 1:
            style = args[1].strip().strip("\"'")
            return f'discord.utils.format_dt({dt}, style="{style}")'
        return f"discord.utils.format_dt({dt})"
    h["timestamp"] = timestamp

    def jump(args):
        return f"{args[0] if args else 'message'}.jump_url"
    h["jump"] = jump

    def avatar(args):
        return f"{args[0] if args else 'user'}.display_avatar.url"
    h["avatar"] = avatar

    def created(args):
        return f"{args[0] if args else 'obj'}.created_at"
    h["created"] = created

    def snowflake_time(args):
        return f"discord.utils.snowflake_time({args[0] if args else '0'})"
    h["snowflake_time"] = snowflake_time

    def escape(args):
        return f"discord.utils.escape_markdown({args[0] if args else 'text'})"
    h["escape"] = escape

    def escape_mentions(args):
        return f"discord.utils.escape_mentions({args[0] if args else 'text'})"
    h["escape_mentions"] = escape_mentions

    def oauth_url(args):
        if args:
            return f"discord.utils.oauth_url({args[0]})"
        return "discord.utils.oauth_url(__bot__.user.id)"
    h["oauth_url"] = oauth_url

    def user_mention(args):
        return 'f"<@{' + (args[0].strip() if args else "uid") + '}>"'
    h["user_mention"] = user_mention

    def channel_mention(args):
        return 'f"<#{' + (args[0].strip() if args else "cid") + '}>"'
    h["channel_mention"] = channel_mention

    def role_mention(args):
        return 'f"<@&{' + (args[0].strip() if args else "rid") + '}>"'
    h["role_mention"] = role_mention

    def spoiler(args):
        return 'f"||{' + (args[0].strip() if args else "text") + '}||"'
    h["spoiler"] = spoiler

    def codeblock(args):
        # @discord.codeblock[code_str]  /  @discord.codeblock[code_str; py]
        text = args[0].strip() if args else "text"
        lang = (args[1].strip().strip("\"'")) if len(args) > 1 else ""
        return 'f"```' + lang + '\\n{' + text + '}\\n```"'
    h["codeblock"] = codeblock

    def progress(args):
        # @discord.progress[value; total]  → "▰▰▰▱▱▱▱▱▱▱"
        # @discord.progress[value; total; 20]  → 20-char bar
        value = args[0] if args else "0"
        total = args[1] if len(args) > 1 else "100"
        if len(args) > 2:
            return f"__progress__({value}, {total}, {args[2].strip()})"
        return f"__progress__({value}, {total})"
    h["progress"] = progress

    # ── SOUNDBOARD (discord.py ≥ 2.4) ────────────────────────
    def fetch_soundboard_sounds(args):
        g = args[0] if args else "guild"
        return f"await {g}.fetch_soundboard_sounds()"
    h["fetch_soundboard_sounds"] = fetch_soundboard_sounds

    def create_soundboard_sound(args):
        # @discord.create_soundboard_sound[guild; "name"; sound_bytes]
        # Optional kwargs: volume=1.0; emoji_id=...; emoji_name=...
        g = args[0] if args else "guild"
        name = _as_str(args[1]) if len(args) > 1 else '"sound"'
        sound = args[2] if len(args) > 2 and "=" not in args[2] else "b''"
        extra_start = 3 if (len(args) > 2 and "=" not in args[2]) else 2
        parts = [f"name={name}", f"sound={sound}"] + _kw(args, extra_start)
        return f"await {g}.create_soundboard_sound({', '.join(parts)})"
    h["create_soundboard_sound"] = create_soundboard_sound

    def edit_soundboard_sound(args):
        # @discord.edit_soundboard_sound[sound; name=...; volume=...; emoji_id=...]
        sound = args[0] if args else "sound"
        return _call(sound, "edit", [], args, 1)
    h["edit_soundboard_sound"] = edit_soundboard_sound

    def delete_soundboard_sound(args):
        return f"await {args[0] if args else 'sound'}.delete()"
    h["delete_soundboard_sound"] = delete_soundboard_sound

    return h


# ─────────────────────────────────────────────────────────────
# PLUGIN ENTRY POINT
# ─────────────────────────────────────────────────────────────

def register(api):
    # Register "discord" as a lib so @discord.X → LibCallNode (code gen)
    api.lib("discord", "discord")

    # Lexer hook: rewrite @discord.BLOCK[... → @_dc_BLOCK[...
    api.lexer_hook(_discord_preprocess)

    # Block commands (event handlers, text commands, slash commands, tasks)
    api.block_command("_dc_on",      _visit_dc_on)
    api.block_command("_dc_command", _visit_dc_command)
    api.block_command("_dc_hybrid",  _visit_dc_hybrid)
    api.block_command("_dc_slash",   _visit_dc_slash)
    api.block_command("_dc_task",    _visit_dc_task)
    api.block_command("_dc_listen",  _visit_dc_listen)
    api.block_command("_dc_view",    _visit_dc_view)
    api.block_command("_dc_button",  _visit_dc_button)
    api.block_command("_dc_cog",     _visit_dc_cog)
    api.block_command("_dc_group",   _visit_dc_group)
    api.block_command("_dc_modal",              _visit_dc_modal)
    api.block_command("_dc_select",             _visit_dc_select)
    api.block_command("_dc_user_select",        _visit_dc_user_select)
    api.block_command("_dc_role_select",        _visit_dc_role_select)
    api.block_command("_dc_channel_select",     _visit_dc_channel_select)
    api.block_command("_dc_mentionable_select", _visit_dc_mentionable_select)
    api.block_command("_dc_context_menu",       _visit_dc_context_menu)
    api.block_command("_dc_error_handler",      _visit_dc_error_handler)

    # Sub-blocks: @on_submit / @body / @autocomplete (with body)
    #   on_submit/body → inside modal/select; autocomplete → inside slash
    api.block_command("on_submit",    _noop_visit)
    api.block_command("body",         _noop_visit)
    api.block_command("autocomplete", _noop_visit)

    # Sub-blocks: @field / @option (one-liners) — inside modal/select
    api.command("field",  _make_oneliner_parser("_dc_field"),  _noop_visit)
    api.command("option", _make_oneliner_parser("_dc_option"), _noop_visit)

    # Sub-blocks: @param / @choice (one-liners) — inside @discord.slash
    api.command("param",  _make_oneliner_parser("_dc_param"),  _noop_visit)
    api.command("choice", _make_oneliner_parser("_dc_choice"), _noop_visit)

    # Lib call handlers for all inline/statement discord commands
    for method, handler in _build_handlers().items():
        api.lib_call("discord", method, handler)

    # @embed[...] — flat inline command (no @discord. prefix needed)
    # Usage: @var[e; @embed["Title"; "Description"; color=0xFF; footer="footer"]]
    api.inline_command("embed", _embed_inline_handler)

    # Inject __embed__ runtime helper so generated code can call it
    # Lazy-imports discord so transpiling works without discord.py installed
    api.inject("__embed__", _cruhon_embed_helper)
    api.inject("__discord_color__", _cruhon_color_helper)

    # Power runtime helpers — pagination, confirm dialog, progress bar
    api.inject("__paginate__", _cruhon_paginate)
    api.inject("__confirm__", _cruhon_confirm)
    api.inject("__progress__", _cruhon_progress)
