# cruhon-discord

Discord botu yazmak için Cruhon eklentisi. **BDFD (Bot Designer For Discord)
gibi kod bilmeyenler bot yapabilir** — ama BDFD'nin aksine, Cruhon'u bilenler
gerçek `class`, `if/else`, döngü, harici API çağrıları ve karmaşık mantık da
kullanabilir. Aynı dil, üç katman.

## Felsefe — 3 katman

| Katman | Kim | Ne yapabilir |
|--------|-----|--------------|
| **1** | Kod bilmeyen | `@discord.command`, `@discord.reply`, `@discord.send` — basit komutlar |
| **2** | Biraz bilen | `@if/@else`, `@for`, `@var` — mantık ekler |
| **3** | Cruhon'u bilen | `@class`, `@http.get` API çağrısı, embed, karmaşık akış |

BDFD katman 1'de kalır. Cruhon üçünü de aynı dosyada destekler.

## Hızlı başlangıç

```clpy
@discord.setup["TOKEN"; prefix="!"; intents="all"]

@discord.command[selam; ctx]
    @discord.reply[ctx; "Merhaba!"]
@end

@discord.run[]
```

Çalıştır: `cruhon run bot.clpy`

Tam örnek için bkz. [`examples/ornek_bot.clpy`](examples/ornek_bot.clpy).

## Komut grupları

- **Kurulum:** `setup`, `run`, `sync_commands`, `start_task`, `stop_task`
- **Olaylar (blok):** `on`, `command`, `slash`, `task`, `listen`
- **Mesaj:** `send`, `reply`, `dm`, `respond`, `defer`, `followup`, `edit`, `delete`, `pin`
- **Tepki:** `react`, `unreact`, `clear_reactions`
- **Embed:** `embed`, `add_field`, `set_footer`, `set_image`, `set_thumbnail`, `set_author`
- **Moderasyon:** `ban`, `unban`, `kick`, `timeout`, `untimeout`, `add_role`, `remove_role`, `nickname`
- **Kanal:** `purge`, `create_text`, `create_voice`, `delete_channel`
- **Arama:** `get_member`, `get_channel`, `get_role`, `find_member`, `me`, `mention`
- **Koruma:** `ignore_self`, `ignore_bots`, `require_role`, `require_guild`
- **Durum:** `status`, `log`, `wait_for`
- **Ses:** `join`, `leave`

Tüm imzalar için `__init__.py` başındaki belge bloğuna bakın.

## Kaçış kapağı (escape hatch)

Bir komut yetmezse `@raw` ile saf discord.py yazabilirsin — bot nesnesi
`__bot__` adıyla erişilebilir:

```clpy
@raw
    @__bot__.command()
    async def gelismis(ctx, *args):
        # tam discord.py gücü
        ...
@end
```

## Gereksinim

`pip install discord.py` — bot kodu çalıştırılırken gerekir.
Transpile (kod üretimi) için gerekmez.
