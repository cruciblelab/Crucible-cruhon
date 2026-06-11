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
- **Events (block):** `on`, `command`, `slash`, `task`, `listen`
- **Messaging:** `send`, `reply`, `dm`, `respond`, `defer`, `followup`, `edit`, `delete`, `pin`
- **Reactions:** `react`, `unreact`, `clear_reactions`
- **Embed:** `embed`, `add_field`, `set_footer`, `set_image`, `set_thumbnail`, `set_author`
- **Moderation:** `ban`, `unban`, `kick`, `timeout`, `untimeout`, `add_role`, `remove_role`, `nickname`
- **Channel:** `purge`, `create_text`, `create_voice`, `delete_channel`
- **Lookup:** `get_member`, `get_channel`, `get_role`, `find_member`, `me`, `mention`
- **Protection:** `ignore_self`, `ignore_bots`, `require_role`, `require_guild`
- **Status:** `status`, `log`, `wait_for`
- **Voice:** `join`, `leave`

For all signatures see the docstring block at the top of `__init__.py`.

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
