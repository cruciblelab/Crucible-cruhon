"""
Test suite for the cruhon-discord plugin.

Verifies the three-layer design:
  Layer 1 — non-coder simple commands (@discord.reply, @discord.send)
  Layer 2 — mid-level logic (@if/@else, @var inside discord blocks)
  Layer 3 — advanced (@class, @for, API fetch, embeds composed with core)

All output is syntax-checked against the Python compiler so we never
ship a plugin that emits broken Python on the supported runtime.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core import mod_loader
from cruhon.core.parser import parse
from cruhon.core.transpiler import transpile


# ─────────────────────────────────────────────────────────────
# FIXTURE — load the plugin once for the whole module
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def _load_discord_mod():
    mod_path = Path(__file__).parent.parent.parent / "mods" / "cruhon-discord"
    mod_loader.load_mod_from_path(mod_path)


def _compile(source: str) -> str:
    """
    Transpile .clpy → Python and assert the result is valid Python.

    Many discord commands emit `await ...` / `return`, which are only legal
    inside a function — exactly where they're used in real bots. So the
    syntax check wraps the output in an `async def` before compiling.
    The returned code is the real, unwrapped output for assertions.
    """
    code = transpile(parse(source))
    indented = "\n".join("    " + line for line in code.splitlines())
    wrapper = "async def __syntax_check__():\n" + (indented if indented.strip() else "    pass")
    compile(wrapper, "<test>", "exec")  # raises SyntaxError on bad output
    return code


# ─────────────────────────────────────────────────────────────
# BOT SETUP
# ─────────────────────────────────────────────────────────────

class TestSetup:
    def test_setup_basic(self):
        code = _compile('@discord.setup["TOKEN"]')
        assert "import discord" in code
        assert "from discord.ext import commands" in code
        assert "commands.Bot(command_prefix='!'" in code
        assert "discord.Intents.default()" in code

    def test_setup_prefix_and_intents(self):
        code = _compile('@discord.setup["TOKEN"; prefix="?"; intents="all"]')
        assert "command_prefix='?'" in code
        assert "discord.Intents.all()" in code

    def test_run(self):
        code = _compile('@discord.setup["T"]\n@discord.run[]')
        assert "__bot__.run(__discord_token__)" in code

    def test_sync_commands(self):
        code = _compile("@discord.sync_commands[]")
        assert "await __bot__.tree.sync()" in code


# ─────────────────────────────────────────────────────────────
# LAYER 1 — non-coder simple commands
# ─────────────────────────────────────────────────────────────

class TestLayer1Simple:
    def test_on_ready(self):
        code = _compile('@discord.on[ready]\n    @discord.log["hi"]\n@end')
        assert "@__bot__.event" in code
        assert "async def on_ready():" in code

    def test_command(self):
        code = _compile('@discord.command[ping; ctx]\n    @discord.reply[ctx; "pong"]\n@end')
        assert "@__bot__.command(name='ping')" in code
        assert "async def ping(ctx):" in code
        assert 'await ctx.reply("pong")' in code

    def test_send(self):
        code = _compile('@discord.send[channel; "hello"]')
        assert 'await channel.send("hello")' in code

    def test_reply(self):
        code = _compile('@discord.reply[ctx; "hi"]')
        assert 'await ctx.reply("hi")' in code

    def test_dm(self):
        code = _compile('@discord.dm[user; "secret"]')
        assert 'await user.send("secret")' in code

    def test_react(self):
        code = _compile('@discord.react[msg; "👍"]')
        assert 'await msg.add_reaction("👍")' in code

    def test_log(self):
        # log must NOT produce nested-quote f-strings (breaks on py<3.12)
        code = _compile('@discord.log["başladı"]')
        assert 'print("[bot]"' in code

    def test_on_message_auto_process_commands(self):
        # message events must auto-call process_commands so text cmds keep working
        code = _compile('@discord.on[message; msg]\n    @discord.log["got it"]\n@end')
        assert "async def on_message(msg):" in code
        assert "await __bot__.process_commands(msg)" in code


# ─────────────────────────────────────────────────────────────
# LAYER 2 — mid-level logic mixed with discord
# ─────────────────────────────────────────────────────────────

class TestLayer2Logic:
    def test_if_else_inside_command(self):
        src = (
            "@discord.command[zar; ctx]\n"
            "    @var[n; random.randint(1, 6)]\n"
            "    @if[n == 6]\n"
            '        @discord.reply[ctx; "altı!"]\n'
            "    @else\n"
            "        @discord.reply[ctx; n]\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "async def zar(ctx):" in code
        assert "n = random.randint(1, 6)" in code
        assert "if n == 6:" in code
        assert "else:" in code

    def test_for_loop_inside_command(self):
        src = (
            "@discord.command[say; ctx]\n"
            "    @for[i; range(3)]\n"
            "        @discord.reply[ctx; i]\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "for i in range(3):" in code
        assert "await ctx.reply(i)" in code

    def test_blocks_stay_flat(self):
        # consecutive @end-terminated blocks must NOT nest into each other
        src = (
            '@discord.command[a; ctx]\n    @discord.reply[ctx; "a"]\n@end\n'
            '@discord.command[b; ctx]\n    @discord.reply[ctx; "b"]\n@end'
        )
        code = _compile(src)
        lines = [l for l in code.splitlines() if l.startswith("async def ")]
        # both defs must be at column 0 (top-level), proving no nesting
        assert "async def a(ctx):" in code
        assert "async def b(ctx):" in code
        assert any(l == "async def b(ctx):" for l in code.splitlines())


# ─────────────────────────────────────────────────────────────
# LAYER 3 — advanced: slash, embeds, API, classes
# ─────────────────────────────────────────────────────────────

class TestLayer3Advanced:
    def test_slash_command(self):
        src = '@discord.slash[hello; "Selam der"; ctx]\n    @discord.respond[ctx; "hi"]\n@end'
        code = _compile(src)
        assert "@__bot__.tree.command(name='hello', description=\"Selam der\")" in code
        assert "async def hello(ctx):" in code
        assert 'await ctx.response.send_message("hi")' in code

    def test_slash_with_param(self):
        src = '@discord.slash[roll; "Zar"; ctx; sides]\n    @discord.respond[ctx; sides]\n@end'
        code = _compile(src)
        assert "async def roll(ctx, sides):" in code

    def test_embed_build(self):
        src = (
            '@var[e; @discord.embed["Başlık"; "Açıklama"; color=0xFF0000]]\n'
            '@discord.add_field[e; "Ad"; "Değer"; inline=False]\n'
            '@discord.set_footer[e; "alt"]'
        )
        code = _compile(src)
        assert 'discord.Embed(title="Başlık", description="Açıklama", color=0xFF0000)' in code
        assert 'e.add_field(name="Ad", value="Değer", inline=False)' in code
        assert 'e.set_footer(text="alt")' in code

    def test_embed_shorthand_positional(self):
        # All positional — use decimal color (hex 0x3498db splits in tokenizer)
        code = _compile('@var[e; @embed["T"; "D"; 3461339; "footer text"; "img.png"]]')
        assert '__embed__(' in code
        assert 'title="T"' in code
        assert 'description="D"' in code
        assert 'color=3461339' in code
        assert 'footer="footer text"' in code
        assert 'image="img.png"' in code

    def test_embed_shorthand_kwargs(self):
        code = _compile('@var[e; @embed["T"; "D"; color=0xFF0000; footer="alt"; author="Yazar"]]')
        assert '__embed__(' in code
        assert 'color=0xFF0000' in code
        assert 'footer="alt"' in code
        assert 'author="Yazar"' in code

    def test_embed_shorthand_empty_skip(self):
        # Empty string positions should be skipped
        code = _compile('@var[e; @embed["T"; "D"; ""; "footer text"]]')
        assert '__embed__(' in code
        assert 'footer="footer text"' in code
        # color not set means not in output
        assert 'color=""' not in code

    def test_embed_shorthand_discord_quick_embed(self):
        # @discord.quick_embed — same engine, @discord. prefix
        code = _compile('@var[e; @discord.quick_embed["T"; "D"; footer="alt"]]')
        assert '__embed__(' in code
        assert 'footer="alt"' in code

    def test_embed_shorthand_footer_icon(self):
        code = _compile('@var[e; @embed["T"; "D"; footer="Alt"; footer_icon="icon.png"]]')
        assert 'footer="Alt"' in code
        assert 'footer_icon="icon.png"' in code

    def test_embed_shorthand_inline_in_send(self):
        # used directly inside send_embed without assigning to var
        code = _compile('@discord.send_embed[channel; @embed["T"; "D"]]')
        assert '__embed__(' in code
        assert 'await channel.send(embed=' in code

    def test_api_fetch_then_embed(self):
        # the killer feature BDFD lacks: real API call feeding a discord embed
        src = (
            "@discord.slash[hava; \"Hava durumu\"; ctx; sehir]\n"
            "    @var[veri; @http.get[\"https://api.example.com\"]]\n"
            "    @var[e; @discord.embed[\"Hava\"; \"detay\"]]\n"
            "    @discord.respond_embed[ctx; e]\n"
            "@end"
        )
        code = _compile(src)
        assert "requests.get(" in code
        assert "discord.Embed(" in code
        assert "await ctx.response.send_message(embed=e)" in code

    def test_class_inside_bot(self):
        # advanced users can define real classes alongside the bot
        src = (
            "@class[Sayac]\n"
            "    @func[__init__; self]\n"
            "        @var[self.n; 0]\n"
            "    @end\n"
            "@end\n"
            '@discord.command[say; ctx]\n    @discord.reply[ctx; "ok"]\n@end'
        )
        code = _compile(src)
        assert "class Sayac:" in code
        assert "async def say(ctx):" in code


# ─────────────────────────────────────────────────────────────
# MODERATION
# ─────────────────────────────────────────────────────────────

class TestModeration:
    def test_ban_simple(self):
        code = _compile("@discord.ban[member]")
        assert "await member.ban(" in code

    def test_ban_with_reason(self):
        code = _compile('@discord.ban[member; reason="spam"; delete_days=1]')
        assert "reason=" in code
        assert "delete_message_days=1" in code

    def test_kick(self):
        code = _compile('@discord.kick[member; reason="kural"]')
        assert "await member.kick(reason=" in code

    def test_timeout_minutes(self):
        code = _compile("@discord.timeout[member; minutes=10]")
        assert "timedelta(minutes=10)" in code
        assert "await member.timeout(" in code

    def test_add_role(self):
        code = _compile("@discord.add_role[member; role]")
        assert "await member.add_roles(role)" in code

    def test_purge(self):
        code = _compile("@discord.purge[channel; 50]")
        assert "await channel.purge(limit=50)" in code


# ─────────────────────────────────────────────────────────────
# GUARDS & LOOKUPS
# ─────────────────────────────────────────────────────────────

class TestGuardsAndLookups:
    def test_ignore_self(self):
        code = _compile("@discord.ignore_self[msg]")
        assert "if msg.author == __bot__.user: return" in code

    def test_ignore_bots(self):
        code = _compile("@discord.ignore_bots[msg]")
        assert "if msg.author.bot: return" in code

    def test_get_member_inline(self):
        code = _compile("@var[m; @discord.get_member[guild; 123]]")
        assert "m = guild.get_member(123)" in code

    def test_get_role_inline(self):
        code = _compile('@var[r; @discord.get_role[guild; "Admin"]]')
        assert 'discord.utils.get(guild.roles, name="Admin")' in code

    def test_status_watching(self):
        code = _compile('@discord.status["yayın"; type="watching"]')
        assert "discord.ActivityType.watching" in code


# ─────────────────────────────────────────────────────────────
# TASKS
# ─────────────────────────────────────────────────────────────

class TestTasks:
    def test_task_minutes(self):
        src = '@discord.task[temizle; minutes=30]\n    @discord.log["temizleniyor"]\n@end'
        code = _compile(src)
        assert "@__discord_tasks__.loop(minutes=30)" in code
        assert "async def temizle():" in code

    def test_start_task(self):
        code = _compile("@discord.start_task[temizle]")
        assert "temizle.start()" in code


# ─────────────────────────────────────────────────────────────
# FULL BOT — end to end
# ─────────────────────────────────────────────────────────────

class TestFullBot:
    def test_complete_bot_compiles(self):
        src = (
            '@discord.setup["TOKEN"; prefix="!"; intents="all"]\n'
            "@discord.on[ready]\n"
            '    @discord.log["hazır"]\n'
            '    @discord.status["Cruhon"; type="watching"]\n'
            "@end\n"
            "@discord.command[selam; ctx]\n"
            '    @discord.reply[ctx; "Merhaba!"]\n'
            "@end\n"
            "@discord.slash[zar; \"Zar at\"; ctx]\n"
            "    @var[n; random.randint(1, 6)]\n"
            "    @discord.respond[ctx; n]\n"
            "@end\n"
            "@discord.run[]"
        )
        code = _compile(src)
        # all three handlers present and flat
        assert "async def on_ready():" in code
        assert "async def selam(ctx):" in code
        assert "async def zar(ctx):" in code
        assert "__bot__.run(__discord_token__)" in code
