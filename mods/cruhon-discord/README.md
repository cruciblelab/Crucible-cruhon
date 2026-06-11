# cruhon-discord

Discord bot plugin for Cruhon. Anyone can write a Discord bot quickly — and
those who know Cruhon can also use real `class`, `if/else`, loops, external
API calls, and complex logic. Same language, three layers.

## Philosophy — 3 Layers

| Layer | Who | What they can do |
|-------|-----|-----------------|
| **1** | Non-programmer | `@discord.command`, `@discord.reply`, `@discord.send` — simple commands |
| **2** | Intermediate | `@if/@else`, `@for`, `@var` — adds logic |
| **3** | Cruhon user | `@class`, `@http.get` API calls, embeds, complex flows |

## Quick Start

```clpy
@discord.setup["TOKEN"; prefix="!"; intents="all"]

@discord.command[hello; ctx]
    @discord.reply[ctx; "Hello!"]
@end

@discord.run[]
```

Run: `cruhon run bot.clpy`

See full example at [`examples/example_bot.clpy`](examples/example_bot.clpy).

## Command Groups

- **Setup:** `setup`, `run`, `sync_commands`, `start_task`, `stop_task`
- **Events (block):** `on` (90+ friendly aliases), `command`, `hybrid`, `slash`, `task` (`time=`/`count=`/`wait_ready=`), `listen`, `error_handler`
- **UI (block):** `view`, `button`, `select` (string), `user_select`, `role_select`, `channel_select`, `mentionable_select`, `modal`, `cog`, `group`, `context_menu`
- **Messaging:** `send`, `reply`, `dm`, `respond`, `respond_ephemeral`, `send_modal`, `defer`, `followup`, `edit`, `edit_embed`, `dm_embed`, `delete`, `pin`
- **Reactions:** `react`, `add_reactions`, `unreact`, `clear_reactions`
- **Embed:** `embed`, `add_field`, `set_footer`, `set_image`, `set_thumbnail`, `set_author`
- **Moderation:** `ban`, `unban`, `kick`, `timeout`, `untimeout`, `add_role`, `remove_role`, `nickname`
- **Channel:** `purge`, `bulk_purge`, `create_text`, `create_voice`, `delete_channel`
- **Lookup:** `get_member`, `get_channel`, `get_role`, `find_member`, `me`, `mention`, `get_guild`, `get_user`
- **Protection:** `ignore_self`, `ignore_bots`, `require_role`, `require_guild`
- **Status:** `status`, `log`, `wait_for`
- **Color:** `color` (`"#hex"` / RGB / named / decimal)
- **Voice:** `join`, `leave`, `play`, `stop_audio`, `pause_audio`, `resume_audio`, `volume`, `is_playing`
- **Inline checks:** `has_role`, `has_perm`, `is_bot_owner`
- **Formatting:** `timestamp`, `jump`, `avatar`, `created`, `escape`, `escape_mentions`, `user_mention`, `channel_mention`, `role_mention`, `spoiler`, `codeblock`, `progress`, `oauth_url`, `snowflake_time`

Slash groups support full option config — `@param`, `@choice`, and
`@autocomplete` work inside `@discord.group` subcommands exactly as they do
in top-level `@discord.slash`. Views accept `persistent=True`
(timeout=None — pair with `custom_id=` buttons and `@discord.add_view`).

For all signatures see the docstring block at the top of `__init__.py`.

## Interactive Components

**Hybrid commands** — one definition that registers as both a prefix command
and a slash command:

```clpy
@discord.hybrid[userinfo; ctx; member]
    @discord.reply[ctx; member.display_name]
@end
```

**Link buttons** — buttons that open a URL have no callback, so the body is
empty (but, like every block, it still closes with `@end`):

```clpy
@discord.view[Links]
    @discord.button[Docs; url="https://example.com"; emoji="📖"]
    @end
    @discord.button[Press; style=green]
        @discord.respond[interaction; "pressed"]
    @end
@end
```

**Slash autocomplete** — suggest options as the user types. Inside the
callback, `current` holds the partial text:

```clpy
@discord.slash[fruit; "Pick a fruit"; interaction]
    @param[name; string; "Fruit name"]
    @autocomplete[name]
        @return[[discord.app_commands.Choice(name=x, value=x)
                 for x in FRUITS if current.lower() in x.lower()]]
    @end
    @discord.respond[interaction; name]
@end
```

**Modal forms** — `@discord.send_modal[interaction; FormClass]` opens a modal
defined with `@discord.modal`.

## @embed — Easy Embed Creation

One-liner full embed. Two syntaxes supported:

**Positional** (order: title → description → color → footer → image → thumbnail → author):
```clpy
@var[e; @embed["Title"; "Description"]]
@var[e; @embed["Title"; "Description"; 3461339; "Footer"]]
@var[e; @embed["Title"; "Description"; ""; "Footer"; "img.png"; "thumb.png"; "Author"]]
```

**Kwargs** (any order, only the fields you need):
```clpy
@var[e; @embed["Title"; "Description"; color=3461339; footer="Footer"; author="Bot"]]
@var[e; @embed["Title"; "Description"; footer="Footer"; footer_icon="icon.png"]]
@var[e; @embed["Title"; "Description"; author="Author"; author_icon="avatar.png"]]
```

**Send directly** (no variable needed):
```clpy
@discord.send_embed[ctx.channel; @embed["Title"; "Description"; footer="Footer"]]
```

**Note — color:** Cruhon's tokenizer splits hex literals (`0x3498db`) at spaces.
Pass color as a decimal (`3461339`) or use kwarg form: `color=0x3498db`
also works because the kwarg value is taken as a raw string.

`@discord.quick_embed[...]` does the same thing (with `@discord.` prefix).

## Escape Hatch

If a command isn't enough, use `@raw` to write plain discord.py — the bot
object is accessible as `__bot__`:

```clpy
@raw
    @__bot__.command()
    async def advanced(ctx, *args):
        # full discord.py power
        ...
@end
```

## Requirements

`pip install discord.py` — required when running bot code.
Not required for transpilation (code generation).
