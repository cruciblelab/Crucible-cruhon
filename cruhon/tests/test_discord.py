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
        code = _compile('@discord.log["started"]')
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
            "@discord.command[roll; ctx]\n"
            "    @var[n; random.randint(1, 6)]\n"
            "    @if[n == 6]\n"
            '        @discord.reply[ctx; "six!"]\n'
            "    @else\n"
            "        @discord.reply[ctx; n]\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "async def roll(ctx):" in code
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
        src = '@discord.slash[hello; "Says hi"; ctx]\n    @discord.respond[ctx; "hi"]\n@end'
        code = _compile(src)
        assert "@__bot__.tree.command(name='hello', description=\"Says hi\")" in code
        assert "async def hello(ctx):" in code
        assert 'await ctx.response.send_message("hi")' in code

    def test_slash_with_param(self):
        src = '@discord.slash[roll; "Roll dice"; ctx; sides]\n    @discord.respond[ctx; sides]\n@end'
        code = _compile(src)
        assert "async def roll(ctx, sides):" in code

    def test_embed_build(self):
        src = (
            '@var[e; @discord.embed["Title"; "Description"; color=0xFF0000]]\n'
            '@discord.add_field[e; "Name"; "Value"; inline=False]\n'
            '@discord.set_footer[e; "footer"]'
        )
        code = _compile(src)
        assert 'discord.Embed(title="Title", description="Description", color=0xFF0000)' in code
        assert 'e.add_field(name="Name", value="Value", inline=False)' in code
        assert 'e.set_footer(text="footer")' in code

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
        # full Python freedom: real API call feeding a discord embed
        src = (
            "@discord.slash[weather; \"Weather info\"; ctx; city]\n"
            "    @var[data; @http.get[\"https://api.example.com\"]]\n"
            "    @var[e; @discord.embed[\"Weather\"; \"details\"]]\n"
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
            "@class[Counter]\n"
            "    @func[__init__; self]\n"
            "        @var[self.n; 0]\n"
            "    @end\n"
            "@end\n"
            '@discord.command[say; ctx]\n    @discord.reply[ctx; "ok"]\n@end'
        )
        code = _compile(src)
        assert "class Counter:" in code
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
        code = _compile('@discord.status["live"; type="watching"]')
        assert "discord.ActivityType.watching" in code


# ─────────────────────────────────────────────────────────────
# TASKS
# ─────────────────────────────────────────────────────────────

class TestTasks:
    def test_task_minutes(self):
        src = '@discord.task[cleanup; minutes=30]\n    @discord.log["cleaning"]\n@end'
        code = _compile(src)
        assert "@__discord_tasks__.loop(minutes=30)" in code
        assert "async def cleanup():" in code

    def test_start_task(self):
        code = _compile("@discord.start_task[cleanup]")
        assert "cleanup.start()" in code


# ─────────────────────────────────────────────────────────────
# FULL BOT — end to end
# ─────────────────────────────────────────────────────────────

class TestFullBot:
    def test_complete_bot_compiles(self):
        src = (
            '@discord.setup["TOKEN"; prefix="!"; intents="all"]\n'
            "@discord.on[ready]\n"
            '    @discord.log["ready"]\n'
            '    @discord.status["Cruhon"; type="watching"]\n'
            "@end\n"
            "@discord.command[hello; ctx]\n"
            '    @discord.reply[ctx; "Hello!"]\n'
            "@end\n"
            "@discord.slash[roll; \"Roll dice\"; ctx]\n"
            "    @var[n; random.randint(1, 6)]\n"
            "    @discord.respond[ctx; n]\n"
            "@end\n"
            "@discord.run[]"
        )
        code = _compile(src)
        # all three handlers present and flat
        assert "async def on_ready():" in code
        assert "async def hello(ctx):" in code
        assert "async def roll(ctx):" in code
        assert "__bot__.run(__discord_token__)" in code


# ─────────────────────────────────────────────────────────────
# NESTED NAMESPACE — full discord.py passthrough
# ─────────────────────────────────────────────────────────────

class TestNestedNamespace:
    def test_ui_button_statement(self):
        code = _compile('@discord.ui.Button[label="Click"]')
        assert 'discord.ui.Button(label="Click")' in code

    def test_ui_button_inline(self):
        code = _compile('@var[b; @discord.ui.Button[label="x"]]')
        assert 'b = discord.ui.Button(label="x")' in code

    def test_color_classmethod_empty_args(self):
        code = _compile('@var[c; @discord.Color.blue[]]')
        assert "c = discord.Color.blue()" in code

    def test_utils_get_multi_arg(self):
        code = _compile('@var[r; @discord.utils.get[guild.roles; name="Admin"]]')
        assert 'r = discord.utils.get(guild.roles, name="Admin")' in code

    def test_app_commands_choice(self):
        code = _compile('@var[ch; @discord.app_commands.Choice[name="A"; value=1]]')
        assert 'ch = discord.app_commands.Choice(name="A", value=1)' in code

    def test_three_level_path(self):
        code = _compile('@var[x; @discord.ext.commands.Bot[]]')
        assert "x = discord.ext.commands.Bot()" in code

    def test_single_level_unchanged(self):
        # @discord.send must NOT be rewritten to __nested
        code = _compile('@discord.send[ch; "hi"]')
        assert "__nested" not in code
        assert 'await ch.send("hi")' in code

    def test_nested_with_variable_arg_not_quoted(self):
        code = _compile('@var[v; @discord.ui.View[timeout=my_timeout]]')
        assert "v = discord.ui.View(timeout=my_timeout)" in code


# ─────────────────────────────────────────────────────────────
# UI — View + Button
# ─────────────────────────────────────────────────────────────

class TestUIView:
    def test_view_class_header(self):
        src = (
            "@discord.view[ConfirmView; timeout=60]\n"
            '    @discord.button[Confirm; style=green]\n'
            '        @discord.respond[interaction; "✅"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "class ConfirmView(discord.ui.View):" in code
        assert "super().__init__(timeout=60)" in code

    def test_button_decorator_and_method(self):
        src = (
            "@discord.view[V]\n"
            '    @discord.button[Confirm; style=green]\n'
            '        @discord.respond[interaction; "ok"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "@discord.ui.button(label=" in code
        assert "discord.ButtonStyle.success" in code
        assert "async def confirm(self, interaction, button):" in code
        assert 'await interaction.response.send_message("ok")' in code

    def test_button_style_aliases(self):
        src = (
            "@discord.view[V]\n"
            '    @discord.button[A; style=red]\n'
            '        @discord.respond[interaction; "a"]\n'
            "    @end\n"
            '    @discord.button[B; style=blurple]\n'
            '        @discord.respond[interaction; "b"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "discord.ButtonStyle.danger" in code
        assert "discord.ButtonStyle.primary" in code

    def test_view_default_timeout(self):
        src = (
            "@discord.view[V]\n"
            '    @discord.button[X; style=green]\n'
            '        @discord.respond[interaction; "x"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "super().__init__(timeout=180)" in code

    def test_two_buttons_distinct_methods(self):
        src = (
            "@discord.view[V]\n"
            '    @discord.button[Yes; style=green]\n'
            '        @discord.respond[interaction; "yes"]\n'
            "    @end\n"
            '    @discord.button[No; style=red]\n'
            '        @discord.respond[interaction; "no"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "async def yes(self, interaction, button):" in code
        assert "async def no(self, interaction, button):" in code


# ─────────────────────────────────────────────────────────────
# COG + GROUP
# ─────────────────────────────────────────────────────────────

class TestCog:
    def test_cog_class_and_init(self):
        src = (
            "@discord.cog[Moderation]\n"
            "    @discord.command[ban; ctx; member]\n"
            "        @discord.ban[member]\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "class Moderation(commands.Cog):" in code
        assert "def __init__(self, bot):" in code
        assert "self.bot = bot" in code

    def test_cog_command_has_self(self):
        src = (
            "@discord.cog[Mod]\n"
            "    @discord.command[ban; ctx; member]\n"
            "        @discord.ban[member]\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "@commands.command(name='ban')" in code
        assert "async def ban(self, ctx, member):" in code
        assert "await member.ban()" in code

    def test_cog_slash_method(self):
        src = (
            "@discord.cog[Util]\n"
            '    @discord.slash[ping; "Ping at"; ctx]\n'
            '        @discord.respond[ctx; "pong"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "discord.app_commands.command(name='ping'" in code
        assert "async def ping(self, ctx):" in code

    def test_add_cog_registration(self):
        code = _compile("@discord.add_cog[Moderation]")
        assert "await __bot__.add_cog(Moderation(__bot__))" in code


class TestGroup:
    def test_group_class_and_instance(self):
        src = (
            '@discord.group[admin; "Admin"]\n'
            '    @discord.slash[ban; "Ban a user"; interaction; member]\n'
            '        @discord.respond[interaction; "ok"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "discord.app_commands.Group" in code
        assert "admin = AdminGroup(name='admin'" in code
        assert "@admin.command(name='ban'" in code
        assert "async def ban(interaction, member):" in code


# ─────────────────────────────────────────────────────────────
# MODAL + SELECT — sub-blocks @field/@option/@on_submit/@body
# ─────────────────────────────────────────────────────────────

class TestModal:
    def test_modal_class_with_title(self):
        src = (
            "@discord.modal[Feedback; FeedbackModal]\n"
            '    @field[Subject; placeholder="Topic"]\n'
            "    @on_submit[interaction]\n"
            '        @discord.respond[interaction; "Thanks"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "class FeedbackModal(discord.ui.Modal, title=" in code
        assert "Feedback" in code
        assert "discord.ui.TextInput(label=" in code
        assert "Topic" in code
        assert "async def on_submit(self, interaction):" in code
        assert 'await interaction.response.send_message("Thanks")' in code

    def test_field_style_and_maxlength(self):
        src = (
            "@discord.modal[F; M]\n"
            '    @field[Message; style=long; max=500]\n'
            "    @on_submit[interaction]\n"
            '        @discord.respond[interaction; "ok"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "discord.TextStyle.long" in code
        assert "max_length=500" in code


class TestSelect:
    def test_select_in_view(self):
        src = (
            "@discord.view[Menu]\n"
            "    @discord.select[Choose a color; min=1; max=1]\n"
            "        @option[Red; value=red]\n"
            "        @option[Blue; value=blue]\n"
            "        @body[interaction; selection]\n"
            '            @discord.respond[interaction; "selected"]\n'
            "        @end\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "class Menu(discord.ui.View):" in code
        assert "@discord.ui.select(placeholder=" in code
        assert "min_values=1" in code
        assert "max_values=1" in code
        assert "discord.SelectOption(label=" in code
        assert "value='red'" in code
        assert "async def" in code
        assert "self, interaction, selection" in code
        assert 'await interaction.response.send_message("selected")' in code

    def test_select_options_count(self):
        src = (
            "@discord.view[M]\n"
            "    @discord.select[Select]\n"
            "        @option[A; value=a]\n"
            "        @option[B; value=b]\n"
            "        @option[C; value=c]\n"
            "        @body[interaction; sel]\n"
            '            @discord.respond[interaction; "x"]\n'
            "        @end\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert code.count("discord.SelectOption(") == 3


# ─────────────────────────────────────────────────────────────
# SHORTCUTS — comprehensive shortcuts
# ─────────────────────────────────────────────────────────────

class TestFaz3Shortcuts:
    def test_fetch_family(self):
        assert "await __bot__.fetch_user(123)" in _compile("@var[u; @discord.fetch_user[123]]")
        assert "await __bot__.fetch_guild(5)" in _compile("@var[g; @discord.fetch_guild[5]]")
        assert "await guild.fetch_member(7)" in _compile("@var[m; @discord.fetch_member[guild; 7]]")

    def test_thread(self):
        assert 'await channel.create_thread(name=' in _compile('@var[t; @discord.create_thread[channel; "discussion"]]')
        assert "await thread.join()" in _compile("@discord.join_thread[thread]")
        assert "await msg.create_thread(name=" in _compile('@var[t; @discord.thread_from[msg; "topic"]]')

    def test_webhook(self):
        assert "await channel.create_webhook(name=" in _compile('@var[w; @discord.create_webhook[channel; "log"]]')
        assert "await wh.send(" in _compile('@discord.send_webhook[wh; "hello"]')

    def test_invite(self):
        assert "await channel.create_invite(" in _compile("@var[i; @discord.create_invite[channel]]")
        assert "await invite.delete()" in _compile("@discord.delete_invite[invite]")

    def test_role_management(self):
        assert "await guild.create_role(name=" in _compile('@var[r; @discord.create_role[guild; "Member"]]')
        assert "await role.delete()" in _compile("@discord.delete_role[role]")

    def test_history_and_audit(self):
        assert "async for" in _compile("@var[h; @discord.history[channel; 50]]")
        assert "audit_logs(limit=10)" in _compile("@var[a; @discord.audit_logs[guild; 10]]")

    def test_file_send(self):
        assert "discord.File(" in _compile('@discord.send_file[channel; "report.pdf"]')

    def test_member_voice(self):
        assert "await member.move_to(channel)" in _compile("@discord.move_to[member; channel]")
        assert "await member.edit(mute=True)" in _compile("@discord.mute[member]")
        assert "await member.move_to(None)" in _compile("@discord.disconnect[member]")

    def test_event(self):
        assert "create_scheduled_event(name=" in _compile('@var[e; @discord.create_event[guild; "Meeting"]]')

    def test_emoji(self):
        assert "create_custom_emoji(name=" in _compile('@var[e; @discord.create_emoji[guild; "blob"; data]]')

    def test_slowmode_and_category(self):
        assert "edit(slowmode_delay=5)" in _compile("@discord.set_slowmode[channel; 5]")
        assert "await guild.create_category(" in _compile('@var[c; @discord.create_category[guild; "Voice"]]')

    def test_sync_tree(self):
        assert "await __bot__.tree.sync()" in _compile("@discord.sync_tree[]")


# ─────────────────────────────────────────────────────────────
# WIDE COVERAGE — stage/forum/automod/ban/guild/sticker
# ─────────────────────────────────────────────────────────────

class TestWideCoverage:
    def test_stage(self):
        assert "create_stage_channel(" in _compile('@var[s; @discord.create_stage[guild; "Stage"]]')
        assert "create_instance(topic=" in _compile('@discord.start_stage[channel; "Live stream"]')

    def test_forum(self):
        assert "await guild.create_forum(" in _compile('@var[f; @discord.create_forum[guild; "support"]]')
        assert "create_thread(name=" in _compile('@discord.create_post[forum; "help"; "content"]')

    def test_bans(self):
        assert "await guild.bulk_ban(users)" in _compile("@discord.bulk_ban[guild; users]")
        assert "async for" in _compile("@var[b; @discord.fetch_bans[guild]]")

    def test_guild_ops(self):
        assert "await guild.fetch_roles()" in _compile("@var[r; @discord.fetch_roles[guild]]")
        assert "prune_members(days=7)" in _compile("@var[p; @discord.prune[guild; 7]]")
        assert "await guild.leave()" in _compile("@discord.leave_guild[guild]")

    def test_sticker(self):
        assert "create_sticker(name=" in _compile('@var[s; @discord.create_sticker[guild; "blob"]]')

    def test_channel_extra(self):
        assert "await channel.clone()" in _compile("@var[c; @discord.clone_channel[channel]]")
        assert "clear_reaction(" in _compile('@discord.clear_reaction[msg; "👍"]')

    def test_automod(self):
        code = _compile('@discord.automod_keyword[guild; "Filter"; bad_words]')
        assert "create_automod_rule(name=" in code
        assert "AutoModTrigger" in code
        assert "keyword_filter=bad_words" in code
        assert "block_message" in code

    def test_member_roles(self):
        assert "await member.add_roles(role1, role2)" in _compile("@discord.add_roles[member; role1; role2]")
        assert "member.roles" in _compile("@var[r; @discord.member_roles[member]]")


# ─────────────────────────────────────────────────────────────
# POWER FEATURES — pagination / confirm / context menu / checks
# ─────────────────────────────────────────────────────────────

class TestPowerFeatures:
    def test_paginate(self):
        assert "await __paginate__(ctx, pages)" in _compile("@discord.paginate[ctx; pages]")
        assert "await __paginate__(ctx, p, 60)" in _compile("@discord.paginate[ctx; p; timeout=60]")

    def test_confirm(self):
        assert 'await __confirm__(ctx, "Delete this?")' in _compile('@var[ok; @discord.confirm[ctx; "Delete this?"]]')

    def test_context_menu_user(self):
        src = (
            "@discord.context_menu[Info; user]\n"
            '    @discord.respond[interaction; "info"]\n'
            "@end"
        )
        code = _compile(src)
        assert "@__bot__.tree.context_menu(name=" in code
        assert "target: discord.Member" in code

    def test_context_menu_message(self):
        src = (
            "@discord.context_menu[Report; message]\n"
            '    @discord.respond[interaction; "reported"]\n'
            "@end"
        )
        code = _compile(src)
        assert "target: discord.Message" in code

    def test_command_cooldown_and_perms(self):
        src = (
            '@discord.command[ban; ctx; member; perms="ban_members"; cooldown=5]\n'
            "    @discord.ban[member]\n"
            "@end"
        )
        code = _compile(src)
        assert "@commands.cooldown(1, 5, commands.BucketType.user)" in code
        assert "@commands.has_permissions(ban_members=True)" in code
        assert "@__bot__.command(name='ban')" in code

    def test_command_guild_and_owner_only(self):
        src = (
            "@discord.command[admin; ctx; guild_only=True; owner_only=True]\n"
            '    @discord.reply[ctx; "ok"]\n'
            "@end"
        )
        code = _compile(src)
        assert "@commands.guild_only()" in code
        assert "@commands.is_owner()" in code

    def test_slash_cooldown(self):
        src = (
            '@discord.slash[daily; "Daily reward"; interaction; cooldown=86400]\n'
            '    @discord.respond[interaction; "reward!"]\n'
            "@end"
        )
        code = _compile(src)
        assert "@discord.app_commands.checks.cooldown(1, 86400)" in code


# ─────────────────────────────────────────────────────────────
# SLASH OPTION CONFIG — @param / @choice
# ─────────────────────────────────────────────────────────────

class TestSlashOptions:
    def test_basic_slash_unchanged(self):
        src = (
            '@discord.slash[ping; "Ping"; interaction]\n'
            '    @discord.respond[interaction; "pong"]\n'
            "@end"
        )
        code = _compile(src)
        assert "async def ping(interaction):" in code
        assert 'await interaction.response.send_message("pong")' in code

    def test_typed_required_param(self):
        src = (
            '@discord.slash[ban; "Ban a user"; interaction]\n'
            '    @param[member; user; "User to ban"]\n'
            '    @discord.respond[interaction; "banned"]\n'
            "@end"
        )
        code = _compile(src)
        assert "async def ban(interaction, member: discord.Member):" in code
        assert "@discord.app_commands.describe(member=" in code

    def test_optional_param(self):
        src = (
            '@discord.slash[say; "Say"; interaction]\n'
            '    @param[text; string; "What to say"]\n'
            '    @param[times; int; "How many"; optional]\n'
            '    @discord.respond[interaction; text]\n'
            "@end"
        )
        code = _compile(src)
        assert "text: str" in code
        assert "times: int = None" in code

    def test_choices(self):
        src = (
            '@discord.slash[mode; "Set mode"; interaction]\n'
            '    @param[level; string; "Level"]\n'
            '    @choice[level; Easy=easy; Hard=hard]\n'
            '    @discord.respond[interaction; level]\n'
            "@end"
        )
        code = _compile(src)
        assert "@discord.app_commands.choices(level=[" in code
        assert "discord.app_commands.Choice(name='Easy', value='easy')" in code
        assert "discord.app_commands.Choice(name='Hard', value='hard')" in code

    def test_param_with_cooldown(self):
        src = (
            '@discord.slash[daily; "Daily"; interaction; cooldown=86400]\n'
            '    @param[choice; string; "Pick"]\n'
            '    @discord.respond[interaction; "ok"]\n'
            "@end"
        )
        code = _compile(src)
        assert "@discord.app_commands.checks.cooldown(1, 86400)" in code
        assert "choice: str" in code


# ─────────────────────────────────────────────────────────────
# LINK BUTTONS — url= buttons (no callback, added via add_item)
# ─────────────────────────────────────────────────────────────

class TestLinkButtons:
    def test_link_button_in_view(self):
        # Link buttons have no callback, but like every block they close with @end
        src = (
            "@discord.view[Links]\n"
            '    @discord.button[Docs; url="https://example.com"; emoji="📖"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "class Links(discord.ui.View):" in code
        # Link button is added in __init__, not as a decorated method
        assert "self.add_item(discord.ui.Button(" in code
        assert "style=discord.ButtonStyle.link" in code
        assert 'url="https://example.com"' in code
        assert "@discord.ui.button" not in code  # no callback decorator

    def test_link_and_callback_buttons_mix(self):
        src = (
            "@discord.view[Mixed]\n"
            '    @discord.button[Visit; url="https://x.io"]\n'
            "    @end\n"
            '    @discord.button[Press; style=green]\n'
            '        @discord.respond[interaction; "pressed"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "self.add_item(discord.ui.Button(" in code      # link button
        assert "async def press(self, interaction, button):" in code  # callback button
        assert "@discord.ui.button(label=" in code

    def test_button_disabled(self):
        src = (
            "@discord.view[V]\n"
            '    @discord.button[X; style=red; disabled=True]\n'
            '        @discord.respond[interaction; "x"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "disabled=True" in code


# ─────────────────────────────────────────────────────────────
# HYBRID COMMANDS — work as both prefix and slash
# ─────────────────────────────────────────────────────────────

class TestHybrid:
    def test_hybrid_basic(self):
        src = (
            "@discord.hybrid[userinfo; ctx; member]\n"
            '    @discord.reply[ctx; "info"]\n'
            "@end"
        )
        code = _compile(src)
        assert "@__bot__.hybrid_command(name='userinfo')" in code
        assert "async def userinfo(ctx, member):" in code

    def test_hybrid_with_description_and_perms(self):
        src = (
            '@discord.hybrid[ban; ctx; member; description="Ban a user"; perms="ban_members"]\n'
            "    @discord.ban[member]\n"
            "@end"
        )
        code = _compile(src)
        assert 'description="Ban a user"' in code
        assert "@commands.has_permissions(ban_members=True)" in code


# ─────────────────────────────────────────────────────────────
# AUTOCOMPLETE — slash option autocomplete callbacks
# ─────────────────────────────────────────────────────────────

class TestAutocomplete:
    def test_autocomplete_callback(self):
        src = (
            '@discord.slash[fruit; "Pick a fruit"; interaction]\n'
            '    @param[name; string; "Fruit name"]\n'
            "    @autocomplete[name]\n"
            "        @var[opts; [\"apple\", \"banana\"]]\n"
            "        @return[[discord.app_commands.Choice(name=o, value=o) for o in opts if current in o]]\n"
            "    @end\n"
            '    @discord.respond[interaction; name]\n'
            "@end"
        )
        code = _compile(src)
        assert "async def fruit(interaction, name: str):" in code
        assert "@fruit.autocomplete('name')" in code
        assert "async def fruit_name_autocomplete(interaction, current: str):" in code

    def test_autocomplete_does_not_pollute_body(self):
        src = (
            '@discord.slash[pick; "Pick"; interaction]\n'
            '    @param[item; string; "Item"]\n'
            "    @autocomplete[item]\n"
            "        @return[[]]\n"
            "    @end\n"
            '    @discord.respond[interaction; item]\n'
            "@end"
        )
        code = _compile(src)
        # the @return inside autocomplete must live in its own function,
        # not in the command body
        assert "async def pick(interaction, item: str):" in code
        assert "async def pick_item_autocomplete(interaction, current: str):" in code


# ─────────────────────────────────────────────────────────────
# MESSAGING/REACTION EXTRAS — send_modal / add_reactions / *_embed
# ─────────────────────────────────────────────────────────────

class TestMessagingExtras:
    def test_send_modal_class(self):
        code = _compile("@discord.send_modal[interaction; FeedbackModal]")
        assert "await interaction.response.send_modal(FeedbackModal())" in code

    def test_send_modal_instance(self):
        code = _compile("@discord.send_modal[interaction; MyModal(arg)]")
        assert "await interaction.response.send_modal(MyModal(arg))" in code

    def test_add_reactions(self):
        code = _compile('@discord.add_reactions[msg; "👍"; "👎"; "❤️"]')
        assert "msg.add_reaction(__e) for __e in [" in code
        assert '"👍"' in code and '"❤️"' in code

    def test_add_reactions_single(self):
        code = _compile('@discord.add_reactions[msg; "👍"]')
        assert "msg.add_reaction(__e) for __e in" in code

    def test_edit_embed(self):
        code = _compile("@discord.edit_embed[message; my_embed]")
        assert "await message.edit(embed=my_embed)" in code

    def test_dm_embed(self):
        code = _compile("@discord.dm_embed[user; my_embed]")
        assert "await user.send(embed=my_embed)" in code


# ─────────────────────────────────────────────────────────────
# EVENT MAP — comprehensive event coverage
# ─────────────────────────────────────────────────────────────

class TestEventMap:
    def test_ready(self):
        src = "@discord.on[ready]\n    @discord.log[\"ready\"]\n@end"
        assert "async def on_ready():" in _compile(src)

    def test_join_alias(self):
        src = "@discord.on[join; member]\n    pass\n@end"
        assert "async def on_member_join(member):" in _compile(src)

    def test_ban_alias(self):
        src = "@discord.on[ban; guild; user]\n    pass\n@end"
        assert "async def on_member_ban(guild, user):" in _compile(src)

    def test_unban_alias(self):
        src = "@discord.on[unban; guild; user]\n    pass\n@end"
        assert "async def on_member_unban(guild, user):" in _compile(src)

    def test_member_update(self):
        src = "@discord.on[member_update; before; after]\n    pass\n@end"
        assert "async def on_member_update(before, after):" in _compile(src)

    def test_role_create(self):
        src = "@discord.on[role_create; role]\n    pass\n@end"
        assert "async def on_guild_role_create(role):" in _compile(src)

    def test_channel_delete(self):
        src = "@discord.on[channel_delete; channel]\n    pass\n@end"
        assert "async def on_guild_channel_delete(channel):" in _compile(src)

    def test_invite_create(self):
        src = "@discord.on[invite_create; invite]\n    pass\n@end"
        assert "async def on_invite_create(invite):" in _compile(src)

    def test_thread_create(self):
        src = "@discord.on[thread_create; thread]\n    pass\n@end"
        assert "async def on_thread_create(thread):" in _compile(src)

    def test_bulk_delete(self):
        src = "@discord.on[bulk_delete; messages]\n    pass\n@end"
        assert "async def on_bulk_message_delete(messages):" in _compile(src)

    def test_automod_action(self):
        src = "@discord.on[automod_action; execution]\n    pass\n@end"
        assert "async def on_automod_action(execution):" in _compile(src)

    def test_poll_vote(self):
        src = "@discord.on[poll_vote_add; payload]\n    pass\n@end"
        assert "async def on_poll_vote_add(payload):" in _compile(src)

    def test_stage_create(self):
        src = "@discord.on[stage_create; stage]\n    pass\n@end"
        assert "async def on_stage_instance_create(stage):" in _compile(src)

    def test_event_create_alias(self):
        src = "@discord.on[event_create; event]\n    pass\n@end"
        assert "async def on_scheduled_event_create(event):" in _compile(src)

    def test_app_error_alias(self):
        src = "@discord.on[app_error; interaction; error]\n    pass\n@end"
        assert "async def on_app_command_error(interaction, error):" in _compile(src)

    def test_unknown_event_passthrough(self):
        # Any event not in the map should pass through as-is
        src = "@discord.on[my_custom_event; data]\n    pass\n@end"
        assert "async def on_my_custom_event(data):" in _compile(src)

    def test_raw_reaction_add(self):
        src = "@discord.on[raw_reaction_add; payload]\n    pass\n@end"
        assert "async def on_raw_reaction_add(payload):" in _compile(src)


# ─────────────────────────────────────────────────────────────
# TYPED SELECTS — user / role / channel / mentionable
# ─────────────────────────────────────────────────────────────

class TestTypedSelects:
    def test_user_select_in_view(self):
        src = (
            "@discord.view[V]\n"
            "    @discord.user_select[Pick a user]\n"
            "        @body[interaction; selection]\n"
            '            @discord.respond[interaction; selection[0].mention]\n'
            "        @end\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "class V(discord.ui.View):" in code
        assert "@discord.ui.user_select(placeholder=" in code
        assert "async def" in code and "self, interaction, selection" in code

    def test_role_select(self):
        src = (
            "@discord.view[V]\n"
            "    @discord.role_select[Pick a role; min=1; max=1]\n"
            "        @body[interaction; sel]\n"
            '            @discord.respond[interaction; "ok"]\n'
            "        @end\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "@discord.ui.role_select(placeholder=" in code
        assert "min_values=1" in code
        assert "max_values=1" in code

    def test_channel_select_with_types(self):
        src = (
            "@discord.view[V]\n"
            "    @discord.channel_select[Pick a channel; channel_types=text,voice]\n"
            "        @body[interaction; sel]\n"
            '            @discord.respond[interaction; "ok"]\n'
            "        @end\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "@discord.ui.channel_select(placeholder=" in code
        assert "channel_types=[discord.ChannelType.text, discord.ChannelType.voice]" in code

    def test_mentionable_select(self):
        src = (
            "@discord.view[V]\n"
            "    @discord.mentionable_select[Pick]\n"
            "        @body[interaction; sel]\n"
            '            @discord.respond[interaction; "ok"]\n'
            "        @end\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "@discord.ui.mentionable_select(placeholder=" in code


# ─────────────────────────────────────────────────────────────
# COG LISTENER + CHECK
# ─────────────────────────────────────────────────────────────

class TestCogListenerAndCheck:
    def test_listener_inside_cog(self):
        src = (
            "@discord.cog[Logging]\n"
            "    @discord.listen[member_join; member]\n"
            '        @discord.log[f"{member} joined"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "class Logging(commands.Cog):" in code
        assert "@commands.Cog.listener()" in code
        assert "async def on_member_join(self, member):" in code

    def test_listener_ban_alias_in_cog(self):
        src = (
            "@discord.cog[Audit]\n"
            "    @discord.listen[ban; guild; user]\n"
            "        pass\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "async def on_member_ban(self, guild, user):" in code

    def test_command_with_check_kwarg(self):
        src = (
            "@discord.command[admin; ctx; check=is_admin]\n"
            '    @discord.reply[ctx; "ok"]\n'
            "@end"
        )
        code = _compile(src)
        assert "@commands.check(is_admin)" in code

    def test_slash_with_check_kwarg(self):
        src = (
            '@discord.slash[admin; "Admin only"; interaction; check=is_admin]\n'
            '    @discord.respond[interaction; "ok"]\n'
            "@end"
        )
        code = _compile(src)
        assert "@discord.app_commands.check(is_admin)" in code

    def test_cog_command_with_perms(self):
        src = (
            "@discord.cog[Mod]\n"
            '    @discord.command[ban; ctx; member; perms="ban_members"]\n'
            "        @discord.ban[member]\n"
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert "@commands.has_permissions(ban_members=True)" in code

    def test_hybrid_inside_cog(self):
        src = (
            "@discord.cog[Utils]\n"
            '    @discord.hybrid[ping; ctx; description="Pong"]\n'
            '        @discord.reply[ctx; "pong"]\n'
            "    @end\n"
            "@end"
        )
        code = _compile(src)
        assert '@commands.hybrid_command(name=\'ping\', description="Pong")' in code
        assert "async def ping(self, ctx):" in code


# ─────────────────────────────────────────────────────────────
# NEW SHORTCUTS — voice / color / misc
# ─────────────────────────────────────────────────────────────

class TestNewShortcuts:
    def test_get_guild(self):
        assert "__bot__.get_guild(123)" in _compile("@var[g; @discord.get_guild[123]]")

    def test_get_user(self):
        assert "__bot__.get_user(456)" in _compile("@var[u; @discord.get_user[456]]")

    def test_send_tts(self):
        assert 'await channel.send("hello", tts=True)' in _compile('@discord.send_tts[channel; "hello"]')

    def test_respond_ephemeral(self):
        code = _compile('@discord.respond_ephemeral[interaction; "secret"]')
        assert 'await interaction.response.send_message("secret", ephemeral=True)' in code

    def test_bulk_purge(self):
        assert "await channel.delete_messages(msgs)" in _compile("@discord.bulk_purge[channel; msgs]")

    def test_color_hex_string(self):
        code = _compile('@var[c; @discord.color["#3498db"]]')
        assert "discord.Color(3447003)" in code

    def test_color_rgb(self):
        code = _compile("@var[c; @discord.color[52; 152; 219]]")
        assert "discord.Color.from_rgb(52, 152, 219)" in code

    def test_color_named(self):
        code = _compile("@var[c; @discord.color[red]]")
        assert "discord.Color.red()" in code

    def test_color_decimal(self):
        code = _compile("@var[c; @discord.color[3447003]]")
        assert "discord.Color(3447003)" in code

    def test_voice_play(self):
        code = _compile('@discord.play[guild; "song.mp3"]')
        assert "voice_client.play(discord.FFmpegPCMAudio(" in code
        assert '"song.mp3"' in code

    def test_voice_play_transformer(self):
        code = _compile('@discord.play[guild; src; volume=True]')
        assert "PCMVolumeTransformer" in code

    def test_voice_stop(self):
        assert "voice_client.stop()" in _compile("@discord.stop_audio[guild]")

    def test_voice_pause_resume(self):
        assert "voice_client.pause()" in _compile("@discord.pause_audio[guild]")
        assert "voice_client.resume()" in _compile("@discord.resume_audio[guild]")

    def test_voice_volume(self):
        assert "source.volume = 0.5" in _compile("@discord.volume[guild; 0.5]")

    def test_is_playing(self):
        assert "is_playing()" in _compile("@var[p; @discord.is_playing[guild]]")
