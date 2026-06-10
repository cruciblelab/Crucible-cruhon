# Cruhon Discord — Tam Python Özgürlüğü Planı

> Hedef: discord.py'nin **%100'ü** Cruhon'dan erişilebilir olsun.
> En ufak detayına kadar Python ile ne yapılıyorsa Cruhon ile de yapılabilsin.
> discord.py 2.7.1 — 253 sınıf · 66 alt modül · ~5000 metod/property

---

## 1. Felsefe — Neden "5000 wrapper" yanlış yol?

stdlib'de öğrendiğimiz ders: **her modülü tek tek sarmalamak yerine passthrough.**
discord.py için de aynısı geçerli. 3 katman:

```
┌─────────────────────────────────────────────────────────┐
│ KATMAN 2 — Block komutları (zor scaffolding)            │
│ @discord.view / button / select / modal / cog / group   │
├─────────────────────────────────────────────────────────┤
│ KATMAN 1 — Ergonomik kısayollar (~60 → ~90 komut)       │
│ @discord.send / ban / embed / thread / webhook / poll    │
├─────────────────────────────────────────────────────────┤
│ KATMAN 0 — Universal passthrough (TAM ÖZGÜRLÜK)         │
│ @discord.X[...]  ·  @discord.ui.Y[...]  ·  düz Python    │
└─────────────────────────────────────────────────────────┘
```

Alt katman ne kadar güçlüyse, üst katmanlar o kadar "şeker" (opsiyonel kolaylık).

---

## 2. Şu an çalışan / çalışmayan (gerçek durum)

| Yetenek | Durum | Mekanizma |
|---|---|---|
| `@discord.Embed["t"; "d"]` → `discord.Embed("t","d")` | ✅ | LibCallNode fallback |
| `@discord.Color.blue[]` | ❌ | nested namespace parse edilemiyor |
| `@discord.ui.Button[...]` | ❌ | nested namespace parse edilemiyor |
| `message.author`, `guild.members` | ✅ | `@var[x; message.author]` düz Python |
| `await msg.add_reaction("👍")` | ✅ | `@var`/`@raw` düz Python |
| View/Button/Modal sınıfı | ⚠️ | `@class[V; discord.ui.View]` el ile yazılır |
| Cog sınıfı | ⚠️ | `@class[C; commands.Cog]` el ile yazılır |
| `@discord.utils.get[...]` | ❌ | nested namespace |

**Kritik tespit:** Tüm Cruhon primitifleri zaten mevcut:
`@class[name; parent]` · `@decorate[expr]` · `@func` · `@var`/`@return`/`@raw` expr passthrough.
Eksik olan **ergonomi ve nested namespace erişimi**.

---

## 3. KATMAN 0 — Universal Passthrough (Çekirdek)

> **⚠️ ÖNEMLİ İLKE: SIFIR CORE DEĞİŞİKLİĞİ.**
> Bir plugin, Cruhon core'una dokunmadan kendini genişletebilmeli.
> Aksi halde başkaları kendi kütüphane plugin'lerini yazamaz.
> discord plugin'i her şeyi **plugin API** ile (lexer_hook / token_hook /
> lib_call / inject) yapar.

### 3.0 Özgürlük zaten var — nested sadece ergonomi

`discord` import edildiği sürece, discord.py'nin **%100'ü** bugün bile
erişilebilir (düz Python passthrough):

```clpy
@var[btn; discord.ui.Button(label="Tıkla", style=discord.ButtonStyle.green)]
@var[v;   discord.ui.View()]
@raw
    v.add_item(btn)
@end
```

Yani tam Python özgürlüğünün **tek ön koşulu = import garantisi** (3.2).
Nested namespace (`@discord.ui.Button[...]`) bunun şekerli kısa hâli.

### 3.1 Çok seviyeli namespace (plugin-only, lexer_hook)

**Sorun:** Lexer `@discord.method` → tek seviye okur; `@discord.ui.Button`
ikinci noktada kırılır.

**Çözüm (core'suz):** Mevcut `_discord_preprocess` lexer_hook'unu genişlet.
Sadece **nokta içeren** path'leri regex ile dönüştür:

```
@discord.ui.Button[label="x"]
   ↓ lexer_hook  (regex: @discord.<path-with-dot>[ )
@discord.__nested["discord.ui.Button"; label="x"]
   ↓ kayıtlı lib_call("discord", "__nested", handler)
discord.ui.Button(label="x")
```

`__nested` handler: args[0] = path string, kalan args = gerçek argümanlar →
`{path}({", ".join(rest)})` emit eder. Hem inline (`@var`) hem statement
bağlamında çalışır (textual rewrite olduğu için).

**Geri uyumluluk:** `@discord.send[...]` içinde nokta yok → regex'e takılmaz,
mevcut fallback ile `discord.send(...)` (aslında özel handler) çalışır.
Block komutları (`@_dc_on` vb.) `@discord.` ile başlamadığı için etkilenmez.

```
@discord.utils.get[guild.roles; name="Admin"]  → discord.utils.get(...)
@discord.Color.blue[]                           → discord.Color.blue()
@discord.app_commands.Choice[name="A"; value=1] → discord.app_commands.Choice(...)
```

**Etki alanı:** SADECE `mods/cruhon-discord/__init__.py`. Core dosyaları
(lexer.py, parser.py, transpiler.py) **değişmez**.

**Opsiyonel ayrı tartışma:** İleride TÜM modüller (`@os.path.join` gibi)
nested kazansın istersek, o zaman core'a genel destek eklenebilir — ama bu
discord için **gerekli değil** ve ayrı bir karardır.

### 3.2 Import garantisi

`@discord.setup[...]` her zaman şunları enjekte etsin:
```python
import discord
import asyncio
from discord.ext import commands
from discord.ext import tasks as __discord_tasks__
from discord import ui as __dc_ui__
from discord import app_commands as __dc_app__
```
Böylece `discord.ui.*`, `app_commands.*`, `commands.*`, `tasks.*` her yerde hazır.

### 3.3 Sonuç — Katman 0 ile erişilen
discord.py'deki **HER** top-level + nested sınıf/fonksiyon/enum:
`discord.Embed`, `discord.File`, `discord.Intents`, `discord.Permissions`,
`discord.AllowedMentions`, `discord.Color.*`, `discord.ButtonStyle.*`,
`discord.ui.*`, `discord.app_commands.*`, `discord.utils.*`, `discord.abc.*` …
Object method/property zaten serbest. → **%100 erişim.**

---

## 4. KATMAN 2 — Block Komutları (interaktif/zor kısımlar)

Tek satırda yapılamayan, sınıf + decorator + callback gerektiren yapılar.

### 4.1 `@discord.view` — buton/menü konteyneri
```
@discord.view[MyView; timeout=60]
    @discord.button[Onayla; style=green]
        @discord.respond[interaction; "Onaylandı ✅"]
    @end
    @discord.button[İptal; style=red]
        @discord.respond[interaction; "İptal edildi ❌"]
    @end
@end
```
→ `class MyView(discord.ui.View)` + `@discord.ui.button` dekoratörlü
async callback metodları. `interaction` parametresi otomatik.

### 4.2 `@discord.button` (view içinde) — callback'li buton
Argümanlar: `label ; style ; emoji ; row ; custom_id`
Stil isimleri friendly: `green/red/blurple/gray` → `discord.ButtonStyle.*`

### 4.3 `@discord.select` — dropdown menü
```
@discord.select[Renk seç; min=1; max=1]
    @option[Kırmızı; value=red; emoji=🔴]
    @option[Mavi; value=blue; emoji=🔵]
    @body[interaction; selection]
        @discord.respond[interaction; f"Seçtin: {selection.values[0]}"]
    @end
@end
```

### 4.4 `@discord.modal` — form/modal
```
@discord.modal[Geri Bildirim; FeedbackModal]
    @field[Başlık; placeholder="Konu"; required=True]
    @field[Mesaj; style=long; max=500]
    @on_submit[interaction]
        @discord.respond[interaction; "Teşekkürler!"]
    @end
@end
```
→ `class FeedbackModal(discord.ui.Modal)` + `TextInput`'lar + `on_submit`.

### 4.5 `@discord.cog` — komut grubu (modüler bot)
```
@discord.cog[Moderation]
    @discord.command[ban; ctx; member]
        @discord.ban[member]
    @end
    @discord.command[kick; ctx; member]
        @discord.kick[member]
    @end
@end
```
→ `class Moderation(commands.Cog)` + metodlar + `bot.add_cog(...)`.

### 4.6 `@discord.group` — slash komut grubu
`/admin ban`, `/admin kick` gibi alt komutlar.
→ `app_commands.Group` veya `commands.GroupCog`.

---

## 5. KATMAN 1 — Kısayol Genişletme (~60 → ~90)

Mevcut friendly komutlar korunur. Yüksek-kullanımlı eksikler eklenir:

| Kategori | Yeni kısayollar |
|---|---|
| Thread | `create_thread`, `archive_thread`, `add_thread_member` |
| Webhook | `create_webhook`, `send_webhook` |
| Invite | `create_invite`, `delete_invite` |
| Poll | `create_poll`, `end_poll` |
| Scheduled | `create_event`, `cancel_event` |
| Audit | `audit_logs` (son N kayıt) |
| Files | `send_file`, `send_files` |
| Permissions | `set_permissions`, `sync_permissions` |
| Emoji/Sticker | `create_emoji`, `delete_emoji` |

---

## 6. Uygulama Sırası (Fazlar)

**Faz 1 — Çekirdek (Katman 0):** ← en kritik
1. Lexer: çok seviyeli `@a.b.c` token zinciri
2. Parser: `_parse_namespace_call` dotted path
3. Transpiler: nested attribute emit + LibCallNode
4. discord mod: import garantisi (ui, app_commands, tasks)
5. Test: her namespace erişim matrisi

**Faz 2 — UI/Cog Block (Katman 2):**
6. `view` / `button` / `select` / `modal` visitor'ları
7. `cog` / `group` visitor'ları
8. Lexer pre-hook: yeni block cmd'leri `_BLOCK_CMDS`'e ekle
9. Test: buton botu, modal form, cog

**Faz 3 — Kısayol (Katman 1):**
10. ~30 yeni friendly handler
11. Test + örnekler

**Faz 4 — Doğrulama & Dokümantasyon:**
12. API_INVENTORY.md erişim matrisi (her sınıf ✅)
13. README, örnek botlar, library.md

---

## 7. Test Stratejisi

- **Transpile testleri** (discord.py kurulu olması gerekmez):
  üretilen Python kodunu string olarak doğrula.
- **Erişim matrisi:** API_INVENTORY'deki 253 sınıfın her biri için
  "Cruhon'dan çağrılabiliyor mu?" otomatik kontrol.
- **Örnek botlar:** moderasyon, interaktif buton, modal form, müzik (ses).

---

## 8. Riskler / Açık Sorular

1. **Regex rewrite kenar durumları** — lexer_hook regex'i nested path'i
   yakalarken tek-seviye, string içi noktalar, iç içe parantezleri
   bozmamalı. (Core değişmiyor; risk sadece plugin içinde, izole.)
2. **`@option` / `@field` / `@body` alt-blokları** — bunlar yeni inline
   komutlar mı yoksa block içi özel parse mı? (Tartışılacak.)
3. **Stil/enum friendly isimleri** — `green` → `ButtonStyle.green` haritası
   ne kadar geniş olsun? (renkler, aktivite tipleri, izinler.)
4. **Ses (voice)** — `discord.FFmpegPCMAudio`, `PCMVolumeTransformer`
   harici bağımlılık (ffmpeg) gerektirir. Passthrough yeterli mi?
5. **Cog dosya ayrımı** — Cog'lar ayrı `.clpy` dosyasına `@use` ile mi,
   yoksa tek dosyada mı? (Modül sistemi ile entegrasyon.)
