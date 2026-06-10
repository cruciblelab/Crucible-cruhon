"""
cruhon-discord v1.0.0
======================
Discord bot plugin for Cruhon.
"Even people who don't know coding can quickly and easily do whatever they want."

━━━ BOT KURULUM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.setup["TOKEN"]
  @discord.setup["TOKEN"; prefix="!"; intents="all"]
  @discord.run[]                       — botu başlat (blocking)
  @discord.sync_commands[]             — slash komutlarını senkronize et

━━━ OLAY YÖNETİCİLERİ (blok komutlar) ━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.on[ready]
  @discord.on[message; msg]
  @discord.on[join; member]            — sunucuya katılma
  @discord.on[leave; member]           — sunucudan ayrılma
  @discord.on[reaction_add; reaction; user]
  @discord.on[reaction_remove; reaction; user]
  @discord.on[error; ctx; error]
  @discord.on[guild_join; guild]
  @discord.on[guild_leave; guild]
  @discord.on[message_edit; before; after]
  @discord.on[message_delete; message]
  ... (tüm discord.py olay isimleri çalışır)

  @discord.command[ping; ctx]           — metin komutu (!ping)
  @discord.command[greet; ctx; user]    — parametreli komut
  @discord.slash[hello; "Merhaba der"; ctx]  — slash komutu (/hello)
  @discord.slash[roll; "Zar at"; ctx; sides]
  @discord.task[cleanup; minutes=30]   — arka plan görevi
  @discord.listen[message; msg]        — ek olay dinleyici

━━━ MESAJLAŞMA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.send[channel; "mesaj"]
  @discord.send[channel; "mesaj"; embed=my_embed]
  @discord.send_embed[channel; embed]
  @discord.reply[ctx; "mesaj"]
  @discord.dm[user; "mesaj"]
  @discord.respond[interaction; "mesaj"]   — slash yanıt
  @discord.respond[interaction; "mesaj"; ephemeral=True]
  @discord.defer[interaction]              — yavaş işlem için beklet
  @discord.followup[interaction; "mesaj"] — defer sonrası gönder
  @discord.edit[message; "yeni içerik"]
  @discord.delete[message]
  @discord.delete[message; delay=5]
  @discord.pin[message]
  @discord.unpin[message]
  @discord.process_commands[msg]          — on_message içinde komutları işle

━━━ TEPKİLER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.react[message; "👍"]
  @discord.unreact[message; "👍"; user]
  @discord.clear_reactions[message]

━━━ EMBED — KOLAY (tek satır, tüm özellikler) ━━━━━━━━━━━━━━━━━━━━
  Pozisyonel sıra: title ; description ; color ; footer ; image ; thumbnail ; author
  Boş geç:  ""  o alan eklenmez

  @var[e; @embed["Başlık"; "Açıklama"]]
  @var[e; @embed["Başlık"; "Açıklama"; 0x3498db]]
  @var[e; @embed["Başlık"; "Açıklama"; 0x3498db; "Alt yazı"]]
  @var[e; @embed["Başlık"; "Açıklama"; ""; "Alt yazı"; "img.png"; "thumb.png"; "Yazar"]]

  Kwargs ile (pozisyonla karışık çalışır):
  @var[e; @embed["Başlık"; "Açıklama"; color=0xFF0000; footer="Alt"; author="Yazar"]]
  @var[e; @embed["Başlık"; "Açıklama"; footer="Alt"; footer_icon="icon.png"]]
  @var[e; @embed["Başlık"; "Açıklama"; author="Yazar"; author_icon="avatar.png"]]

  @discord.quick_embed — aynı şey, @discord. önekiyle:
  @var[e; @discord.quick_embed["Başlık"; "Açıklama"; footer="Alt"]]

━━━ EMBED — DETAYLI (tek tek ayarla) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @var[e; @discord.embed["Başlık"; "Açıklama"]]
  @var[e; @discord.embed["Başlık"; "Açıklama"; color=0xFF0000]]
  @discord.add_field[e; "Alan Adı"; "Alan Değeri"]
  @discord.add_field[e; "Alan Adı"; "Alan Değeri"; inline=False]
  @discord.set_footer[e; "Alt yazı"]
  @discord.set_footer[e; "Alt yazı"; icon="icon_url"]
  @discord.set_image[e; "resim_url"]
  @discord.set_thumbnail[e; "küçük_resim_url"]
  @discord.set_author[e; "Yazar Adı"]
  @discord.set_author[e; "Yazar Adı"; icon="avatar_url"]

━━━ MODERASİON ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.ban[member]
  @discord.ban[member; reason="Spam"; delete_days=1]
  @discord.unban[guild; user]
  @discord.kick[member]
  @discord.kick[member; reason="Kural ihlali"]
  @discord.timeout[member; minutes=10]
  @discord.timeout[member; hours=1]
  @discord.untimeout[member]
  @discord.add_role[member; role]
  @discord.remove_role[member; role]
  @discord.nickname[member; "Yeni İsim"]

━━━ KANAL İŞLEMLERİ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.purge[channel; 10]
  @discord.create_text[guild; "kanal-adi"]
  @discord.create_voice[guild; "ses-kanalı"]
  @discord.delete_channel[channel]

━━━ ARAMA (inline ifade) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @var[m; @discord.get_member[guild; 123456789]]
  @var[ch; @discord.get_channel[guild; 987654321]]
  @var[r; @discord.get_role[guild; "Admin"]]
  @var[u; @discord.find_member[guild; "kullanici_adi"]]
  @var[me; @discord.me[]]

━━━ KORUMA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.ignore_self[msg]            — bot kendi mesajını yoksay
  @discord.ignore_bots[msg]            — tüm bot mesajlarını yoksay
  @discord.require_role[ctx; "Admin"] — rol yoksa durdur
  @discord.require_guild[]             — DM'de çalışmasın

━━━ DURUM & ÇEŞİTLİ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.status["Oyun oynuyor"]
  @discord.status["Yayın izliyor"; type="watching"]
  @discord.status["Müzik dinliyor"; type="listening"]
  @discord.log["mesaj"]               — [bot] önekiyle yazdır
  @discord.wait_for["message"; timeout=30]
  @discord.wait_for["message"; timeout=30; check=my_check_fn]
  @discord.start_task[task_adi]       — arka plan görevini başlat
  @discord.stop_task[task_adi]        — arka plan görevini durdur

━━━ SES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @discord.join[voice_channel]        — ses kanalına katıl
  @discord.leave[guild]               — ses kanalından ayrıl
"""

from __future__ import annotations

import re


# ─────────────────────────────────────────────────────────────
# BLOCK COMMANDS — rewritten by lexer hook before tokenization
# ─────────────────────────────────────────────────────────────

_BLOCK_CMDS = {"on", "command", "slash", "task", "listen",
               "view", "button", "cog", "group"}

# Friendly button style names → discord.ButtonStyle member (komple geniş)
_BUTTON_STYLES = {
    "primary": "primary", "blurple": "primary", "blue": "primary",
    "secondary": "secondary", "grey": "secondary", "gray": "secondary",
    "success": "success", "green": "success",
    "danger": "danger", "red": "danger",
    "link": "link", "url": "link",
}


def _slug(s: str) -> str:
    """Bir etiketten geçerli Python tanımlayıcısı üret (buton metod adı)."""
    s = (s or "").strip().strip("\"'")
    s = re.sub(r"\W+", "_", s, flags=re.UNICODE).strip("_").lower()
    if not s or not (s[0].isalpha() or s[0] == "_"):
        s = "btn_" + s
    return s or "button"


def _style_expr(raw: str) -> str:
    """style=green → discord.ButtonStyle.success (bilinmeyen → olduğu gibi)."""
    key = raw.strip().strip("\"'").lower()
    member = _BUTTON_STYLES.get(key)
    if member:
        return f"discord.ButtonStyle.{member}"
    # Kullanıcı zaten discord.ButtonStyle.X yazdıysa veya bilinmeyen ad
    return raw.strip() if "." in raw else f"discord.ButtonStyle.{key}"

# Nested namespace: @discord.ui.Button[  /  @discord.utils.get[  /  @discord.Color.blue[
# Matches @discord. followed by 2+ dotted segments, then "[".
# Single-level (@discord.send[) has no inner dot → not matched.
_NESTED_RE = re.compile(r"@discord\.([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)\[")

# Friendly event names → discord.py event function names
_EVENT_MAP = {
    "ready":           "ready",
    "message":         "message",
    "join":            "member_join",
    "leave":           "member_remove",
    "member_join":     "member_join",
    "member_remove":   "member_remove",
    "reaction_add":    "reaction_add",
    "reaction_remove": "reaction_remove",
    "error":           "command_error",
    "guild_join":      "guild_join",
    "guild_leave":     "guild_remove",
    "message_edit":    "message_edit",
    "message_delete":  "message_delete",
    "typing":          "typing",
    "voice":           "voice_state_update",
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


def _visit_dc_command(transpiler, node):
    """
    @discord.command[ping; ctx]
    @discord.command[greet; ctx; user; aliases="hi,hey"]
    → @__bot__.command(name=...) + async def <name>(ctx, ...):
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
        f"{indent}async def {name}({params_str}):",
        body_code if body_code.strip() else f"{indent}    pass",
    ]
    return "\n".join(lines)


def _visit_dc_slash(transpiler, node):
    """
    @discord.slash[hello; "Merhaba der"; ctx]
    @discord.slash[roll; "Zar at"; ctx; sides]
    → @__bot__.tree.command(name=..., description=...) + async def <name>(<params>):
    """
    args = node.args

    name = args[0].strip() if args else "slash_cmd"
    description = args[1].strip() if len(args) > 1 else f'"{args[0].strip() if args else "command"}"'
    ctx = args[2].strip() if len(args) > 2 else "interaction"
    extra_params = [a.strip() for a in args[3:]]
    params_str = ", ".join([ctx] + extra_params)

    indent = "    " * transpiler._indent
    body_code = transpiler._block(node.body)

    lines = [
        f"{indent}@__bot__.tree.command(name={name!r}, description={description})",
        f"{indent}async def {name}({params_str}):",
        body_code if body_code.strip() else f"{indent}    pass",
    ]
    return "\n".join(lines)


def _visit_dc_task(transpiler, node):
    """
    @discord.task[cleanup; minutes=30]
    @discord.task[heartbeat; seconds=10]
    → @__discord_tasks__.loop(...) + async def <name>():
    """
    args = node.args
    kwargs = node.kwargs

    func_name = args[0].strip() if args else "background_task"

    # Time interval — kwarg takes priority, then second positional arg (minutes)
    if "minutes" in kwargs:
        loop_kw = f"minutes={kwargs['minutes']}"
    elif "seconds" in kwargs:
        loop_kw = f"seconds={kwargs['seconds']}"
    elif "hours" in kwargs:
        loop_kw = f"hours={kwargs['hours']}"
    elif len(args) > 1:
        loop_kw = f"minutes={args[1].strip()}"
    else:
        loop_kw = "minutes=5"

    indent = "    " * transpiler._indent
    body_code = transpiler._block(node.body)

    lines = [
        f"{indent}@__discord_tasks__.loop({loop_kw})",
        f"{indent}async def {func_name}():",
        body_code if body_code.strip() else f"{indent}    pass",
    ]
    return "\n".join(lines)


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
# UI BLOCK VISITORS — View / Button (interaktif bileşenler)
# ─────────────────────────────────────────────────────────────

def _render_button(transpiler, btn):
    """
    @discord.button[Onayla; style=green; emoji="✅"; row=0]
        <callback gövdesi>
    @end
    → @discord.ui.button(...) + async def <slug>(self, interaction, button):
    callback gövdesinde `interaction` kullanılır.
    """
    args = btn.args
    kw = btn.kwargs
    label = args[0].strip() if args else '"Button"'
    name = _slug(label)

    deco = [f"label={label}"]
    if "style" in kw:
        deco.append(f"style={_style_expr(kw['style'])}")
    if "emoji" in kw:
        deco.append(f"emoji={kw['emoji'].strip()}")
    if "row" in kw:
        deco.append(f"row={kw['row'].strip()}")
    if "custom_id" in kw:
        deco.append(f"custom_id={kw['custom_id'].strip()}")

    base = "    " * transpiler._indent
    body_code = transpiler._block(btn.body)  # _indent+1 seviyesinde render
    return "\n".join([
        f"{base}@discord.ui.button({', '.join(deco)})",
        f"{base}async def {name}(self, interaction, button):",
        body_code if body_code.strip() else f"{base}    pass",
    ])


def _visit_dc_button(transpiler, node):
    """Tek başına @discord.button — sınıf gövdesi bağlamında metod üretir."""
    return _render_button(transpiler, node)


def _visit_dc_view(transpiler, node):
    """
    @discord.view[ConfirmView; timeout=60]
        @discord.button[...] ... @end
    @end
    → class ConfirmView(discord.ui.View): __init__ + buton metodları
    """
    from cruhon.core.ast_nodes import PluginBlockNode

    name = (node.args[0].strip().strip("\"'")) if node.args else "MyView"
    timeout = node.kwargs.get("timeout", "180").strip()

    base = "    " * transpiler._indent
    lines = [
        f"{base}class {name}(discord.ui.View):",
        f"{base}    def __init__(self):",
        f"{base}        super().__init__(timeout={timeout})",
    ]

    transpiler._indent += 1  # sınıf gövdesi seviyesi
    try:
        for child in node.body:
            if isinstance(child, PluginBlockNode) and child.plugin_name == "_dc_button":
                lines.append(_render_button(transpiler, child))
            else:
                rendered = child.accept(transpiler)
                if rendered:
                    lines.append(rendered)
    finally:
        transpiler._indent -= 1

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# COG BLOCK VISITOR — modüler bot (komut grubu sınıfı)
# ─────────────────────────────────────────────────────────────

def _render_cog_method(transpiler, child):
    """Cog içindeki @discord.command / @discord.slash → self'li metod."""
    args = child.args
    base = "    " * transpiler._indent

    if child.plugin_name == "_dc_command":
        name = args[0].strip() if args else "cmd"
        ctx = args[1].strip() if len(args) > 1 else "ctx"
        extra = [a.strip() for a in args[2:]]
        params = ", ".join(["self", ctx] + extra)
        body_code = transpiler._block(child.body)
        return "\n".join([
            f"{base}@commands.command(name={name!r})",
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
            f"{base}async def {name}({params}):",
            body_code if body_code.strip() else f"{base}    pass",
        ])

    # Diğer düğümleri olduğu gibi render et
    return child.accept(transpiler)


def _visit_dc_cog(transpiler, node):
    """
    @discord.cog[Moderation]
        @discord.command[ban; ctx; member] ... @end
    @end
    → class Moderation(commands.Cog): __init__(self, bot) + metodlar
    Kayıt: @discord.add_cog[Moderation] (on_ready/setup içinde).
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
    @discord.group[admin; "Yönetici komutları"]
        @discord.slash[ban; "Yasakla"; interaction; member] ... @end
    @end
    → app_commands.Group alt sınıfı + alt komut metodları.
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
    # Alt komutları @<group>.command dekoratörüyle bağla
    for child in node.body:
        if isinstance(child, type(node)) and child.plugin_name == "_dc_slash":
            cargs = child.args
            cname = cargs[0].strip() if cargs else "sub"
            cdesc = cargs[1].strip() if len(cargs) > 1 else repr(cname)
            ctx = cargs[2].strip() if len(cargs) > 2 else "interaction"
            extra = [a.strip() for a in cargs[3:]]
            params = ", ".join([ctx] + extra)
            body_code = transpiler._block(child.body)
            lines.append(f"{base}@{name}.command(name={cname!r}, description={cdesc})")
            lines.append(f"{base}async def {cname}({params}):")
            lines.append(body_code if body_code.strip() else f"{base}    pass")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# @embed / @discord.quick_embed — tek satırda tam embed
# ─────────────────────────────────────────────────────────────

# Pozisyonel arg sırası: title description color footer image thumbnail author
_EMBED_POSITIONS = ("title", "description", "color", "footer", "image", "thumbnail", "author")


def _embed_code(args: list) -> str:
    """
    Ortak kod üretici — hem @embed[...] hem @discord.quick_embed[...] kullanır.

    Desteklenen biçimler:
      Pozisyonel:   @embed["T"; "D"; 0xFF; "footer"; "img"; "thumb"; "author"]
      Kwargs:       @embed["T"; "D"; color=0xFF; footer="f"; author="a"]
      Karışık:      @embed["T"; "D"; footer="f"]   (kalan pozisyonlar atlanır)

    Boş string ("" veya '') → o alan eklenmez.
    Üretilen Python:  __embed__(title=..., description=..., ...)
    __embed__ runtime'da api.inject() ile enjekte edilmiş yardımcı fonksiyondur.
    """
    positional = []
    kwargs: dict[str, str] = {}

    for a in args:
        a = a.strip()
        # kwarg tespiti: identifier = değer
        eq = a.find("=")
        if eq > 0 and a[:eq].strip().replace("_", "").isalpha():
            k = a[:eq].strip()
            v = a[eq + 1:].strip()
            kwargs[k] = v
        else:
            positional.append(a)

    # Pozisyonel argları sözlüğe çevir (kwargs varsa atlanır)
    for i, val in enumerate(positional):
        if i >= len(_EMBED_POSITIONS):
            break
        field = _EMBED_POSITIONS[i]
        if field not in kwargs:
            kwargs[field] = val

    # Boş string olanları çıkar: "" veya ''
    kwargs = {k: v for k, v in kwargs.items() if v not in ('""', "''", "")}

    if not kwargs:
        return "__embed__()"

    parts = [f"{k}={v}" for k, v in kwargs.items()]
    return f"__embed__({', '.join(parts)})"


def _cruhon_embed_helper(**kwargs):
    """
    Runtime yardımcısı — api.inject() ile __embed__ adıyla enjekte edilir.
    Discord kurulu olmadan transpile çalışır; embed oluşturma runtime'da yapılır.
    """
    import discord as _discord

    # Renk
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


def _embed_inline_handler(parser):
    """
    api.inline_command("embed") kaydı için handler.
    @embed[...] → @var[e; @embed["T";"D"]] gibi inline kullanımda tetiklenir.
    """
    parser.advance()          # @embed token'ını tüket
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

    # ── BOT KURULUM ───────────────────────────────────────────

    def setup(args):
        token = args[0] if args else '""'
        prefix = "!"
        intents_name = "default"
        for a in args[1:]:
            a = a.strip()
            if a.startswith("prefix="):
                prefix = a[7:].strip().strip("\"'")
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
            f"__bot__ = commands.Bot(command_prefix={prefix!r}, intents={intents})"
        )
    h["setup"] = setup

    def run(args):
        return "__bot__.run(__discord_token__)"
    h["run"] = run

    def sync_commands(args):
        return "await __bot__.tree.sync()"
    h["sync_commands"] = sync_commands

    def add_cog(args):
        # @discord.add_cog[Moderation] — async bağlamda (on_ready/setup) kullan
        name = args[0].strip() if args else "MyCog"
        return f"await __bot__.add_cog({name}(__bot__))"
    h["add_cog"] = add_cog

    def add_view(args):
        # @discord.add_view[ConfirmView] — kalıcı view kaydı
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

    # ── MESAJLAŞMA ────────────────────────────────────────────

    def send(args):
        if not args:
            return 'await ctx.send("")'
        channel = args[0]
        if len(args) == 1:
            return f"await {channel}.send()"
        # Collect kwargs from remaining args
        extra_kw = [a.strip() for a in args[2:] if "=" in a.strip()]
        text = args[1]
        # If text is a kwarg (e.g. embed=x), shift
        if "=" in text.strip() and text.strip().split("=")[0].isidentifier():
            kw_str = ", ".join([text.strip()] + extra_kw)
            return f"await {channel}.send({kw_str})"
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
        text = args[1] if len(args) > 1 else '""'
        extra_kw = [a.strip() for a in args[2:] if "=" in a.strip()]
        if extra_kw:
            return f"await {target}.reply({text}, {', '.join(extra_kw)})"
        return f"await {target}.reply({text})"
    h["reply"] = reply

    def dm(args):
        user = args[0] if args else "user"
        text = args[1] if len(args) > 1 else '""'
        return f"await {user}.send({text})"
    h["dm"] = dm

    def respond(args):
        interaction = args[0] if args else "interaction"
        text = args[1] if len(args) > 1 else '""'
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
        text = args[1] if len(args) > 1 else '""'
        extra_kw = [a.strip() for a in args[2:] if "=" in a.strip()]
        if extra_kw:
            return f"await {interaction}.followup.send({text}, {', '.join(extra_kw)})"
        return f"await {interaction}.followup.send({text})"
    h["followup"] = followup

    def edit(args):
        message = args[0] if args else "message"
        content = args[1] if len(args) > 1 else '""'
        return f"await {message}.edit(content={content})"
    h["edit"] = edit

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

    # ── TEPKİLER ──────────────────────────────────────────────

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

    def clear_reactions(args):
        return f"await {args[0] if args else 'message'}.clear_reactions()"
    h["clear_reactions"] = clear_reactions

    # ── EMBED ──────────────────────────────────────────────────

    def quick_embed(args):
        """@discord.quick_embed[...] — @embed ile aynı, @discord. önekiyle."""
        return _embed_code(args)
    h["quick_embed"] = quick_embed

    def embed(args):
        title = args[0] if args else '""'
        description = args[1] if len(args) > 1 else '""'
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
        name = args[1] if len(args) > 1 else '""'
        value = args[2] if len(args) > 2 else '""'
        inline = True
        for a in args[3:]:
            if a.strip() == "inline=False":
                inline = False
        return f"{emb}.add_field(name={name}, value={value}, inline={inline})"
    h["add_field"] = add_field

    def set_footer(args):
        emb = args[0] if args else "embed"
        text = args[1] if len(args) > 1 else '""'
        for a in args[2:]:
            if a.strip().startswith("icon="):
                return f"{emb}.set_footer(text={text}, icon_url={a.strip()[5:]})"
        return f"{emb}.set_footer(text={text})"
    h["set_footer"] = set_footer

    def set_image(args):
        emb = args[0] if args else "embed"
        url = args[1] if len(args) > 1 else '""'
        return f"{emb}.set_image(url={url})"
    h["set_image"] = set_image

    def set_thumbnail(args):
        emb = args[0] if args else "embed"
        url = args[1] if len(args) > 1 else '""'
        return f"{emb}.set_thumbnail(url={url})"
    h["set_thumbnail"] = set_thumbnail

    def set_author(args):
        emb = args[0] if args else "embed"
        name = args[1] if len(args) > 1 else '""'
        for a in args[2:]:
            if a.strip().startswith("icon="):
                return f"{emb}.set_author(name={name}, icon_url={a.strip()[5:]})"
        return f"{emb}.set_author(name={name})"
    h["set_author"] = set_author

    # ── MODERASİON ────────────────────────────────────────────

    def ban(args):
        member = args[0] if args else "member"
        kw_parts = []
        for a in args[1:]:
            a = a.strip()
            if a.startswith("reason="):
                kw_parts.append(f"reason={a[7:]}")
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
                return f"await {guild}.unban({user}, reason={a.strip()[7:]})"
        return f"await {guild}.unban({user})"
    h["unban"] = unban

    def kick(args):
        member = args[0] if args else "member"
        for a in args[1:]:
            if a.strip().startswith("reason="):
                return f"await {member}.kick(reason={a.strip()[7:]})"
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
        nick = args[1] if len(args) > 1 else '""'
        return f"await {member}.edit(nick={nick})"
    h["nickname"] = nickname

    # ── KANALLAR ──────────────────────────────────────────────

    def purge(args):
        channel = args[0] if args else "channel"
        limit = args[1] if len(args) > 1 else "10"
        return f"await {channel}.purge(limit={limit})"
    h["purge"] = purge

    def create_text(args):
        guild = args[0] if args else "guild"
        name = args[1] if len(args) > 1 else '"yeni-kanal"'
        for a in args[2:]:
            if a.strip().startswith("category="):
                return f"await {guild}.create_text_channel({name}, category={a.strip()[9:]})"
        return f"await {guild}.create_text_channel({name})"
    h["create_text"] = create_text

    def create_voice(args):
        guild = args[0] if args else "guild"
        name = args[1] if len(args) > 1 else '"yeni-ses"'
        return f"await {guild}.create_voice_channel({name})"
    h["create_voice"] = create_voice

    def delete_channel(args):
        return f"await {args[0] if args else 'channel'}.delete()"
    h["delete_channel"] = delete_channel

    # ── ARAMA (expression olarak döner) ───────────────────────

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
        name = args[1] if len(args) > 1 else '""'
        return f"discord.utils.get({guild}.roles, name={name})"
    h["get_role"] = get_role

    def find_member(args):
        guild = args[0] if args else "guild"
        name = args[1] if len(args) > 1 else '""'
        return f"discord.utils.find(lambda __m__: __m__.name == {name}, {guild}.members)"
    h["find_member"] = find_member

    def me(args):
        return "__bot__.user"
    h["me"] = me

    def mention(args):
        return f"{args[0] if args else 'member'}.mention"
    h["mention"] = mention

    # ── KORUMA ────────────────────────────────────────────────

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
        role = args[1] if len(args) > 1 else '"member"'
        err = args[2] if len(args) > 2 else '"Bu komutu kullanmak için yetkiniz yok."'
        return (
            f"if not discord.utils.get({ctx}.author.roles, name={role}): "
            f"await {ctx}.send({err}); return"
        )
    h["require_role"] = require_role

    def require_guild(args):
        ctx = args[0] if args else "ctx"
        return (
            f'if {ctx}.guild is None: '
            f'await {ctx}.send("Bu komut sadece sunucularda kullanılabilir."); return'
        )
    h["require_guild"] = require_guild

    # ── DURUM & ÇEŞİTLİ ──────────────────────────────────────

    def status(args):
        text = args[0] if args else '""'
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
            url = args[2] if len(args) > 2 else '""'
            return (
                f"await __bot__.change_presence("
                f"activity=discord.Streaming(name={text}, url={url}))"
            )
        return f"await __bot__.change_presence(activity=discord.Game(name={text}))"
    h["status"] = status

    def log(args):
        text = args[0] if args else '""'
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

    # ── SES ───────────────────────────────────────────────────

    def join(args):
        channel = args[0] if args else "voice_channel"
        return f"await {channel}.connect()"
    h["join"] = join

    def leave(args):
        guild = args[0] if args else "guild"
        return f"await {guild}.voice_client.disconnect()"
    h["leave"] = leave

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
    api.block_command("_dc_slash",   _visit_dc_slash)
    api.block_command("_dc_task",    _visit_dc_task)
    api.block_command("_dc_listen",  _visit_dc_listen)
    api.block_command("_dc_view",    _visit_dc_view)
    api.block_command("_dc_button",  _visit_dc_button)
    api.block_command("_dc_cog",     _visit_dc_cog)
    api.block_command("_dc_group",   _visit_dc_group)

    # Lib call handlers for all inline/statement discord commands
    for method, handler in _build_handlers().items():
        api.lib_call("discord", method, handler)

    # @embed[...] — flat inline command (no @discord. prefix needed)
    # Usage: @var[e; @embed["Başlık"; "Açıklama"; color=0xFF; footer="alt"]]
    api.inline_command("embed", _embed_inline_handler)

    # Inject __embed__ runtime helper so generated code can call it
    # Lazy-imports discord so transpiling works without discord.py installed
    api.inject("__embed__", _cruhon_embed_helper)
