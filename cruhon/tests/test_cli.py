"""
Tests for the cruhon CLI commands: repl, docs, fmt, run --watch.

The interactive/loop parts (input loop, watch polling) are driven through
their pure helper functions so the tests stay deterministic and fast.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon import cli
from cruhon.core.parser import parse, get_parser
from cruhon.core.transpiler import transpile
from cruhon.core.mod_loader import load_all_mods, list_block_commands


@pytest.fixture(scope="module", autouse=True)
def _mods():
    load_all_mods(Path(__file__).parent.parent.parent)


def _openers():
    parser = get_parser()
    openers = set(parser._block_commands.keys()) - {"decorator"}
    for cmds in list_block_commands().values():
        openers.update(cmds)
    return openers


# ─────────────────────────────────────────────────────────────
# fmt — _format_clpy
# ─────────────────────────────────────────────────────────────

class TestFormat:
    def test_reindents_nested_blocks(self):
        messy = (
            "@for[i; range(3)]\n"
            "@print[{i}]\n"
            "@end\n"
        )
        out = cli._format_clpy(messy, _openers())
        assert out == (
            "@for[i; range(3)]\n"
            "    @print[{i}]\n"
            "@end\n"
        )

    def test_else_dedents_its_own_line(self):
        src = (
            "@if[x]\n"
            "@print[a]\n"
            "@else\n"
            "@print[b]\n"
            "@end\n"
        )
        out = cli._format_clpy(src, _openers())
        lines = out.splitlines()
        assert lines[0] == "@if[x]"
        assert lines[1] == "    @print[a]"
        assert lines[2] == "@else"
        assert lines[3] == "    @print[b]"
        assert lines[4] == "@end"

    def test_already_formatted_is_idempotent(self):
        good = (
            "@func[greet; name]\n"
            "    @return[name]\n"
            "@end\n"
        )
        out = cli._format_clpy(good, _openers())
        assert out == good

    def test_blank_lines_preserved(self):
        src = "@var[x; 1]\n\n@var[y; 2]\n"
        out = cli._format_clpy(src, _openers())
        assert out == "@var[x; 1]\n\n@var[y; 2]\n"

    def test_custom_indent_width(self):
        src = "@for[i; xs]\n@print[{i}]\n@end\n"
        out = cli._format_clpy(src, _openers(), indent=2)
        assert "  @print[{i}]" in out

    def test_deeply_nested(self):
        src = "@for[i; a]\n@for[j; b]\n@print[{j}]\n@end\n@end\n"
        out = cli._format_clpy(src, _openers())
        lines = out.splitlines()
        assert lines[2] == "        @print[{j}]"

    def test_formatted_output_still_runs(self, capsys):
        from cruhon.core.runner import run_source
        messy = "@for[i; range(2)]\n@print[{i}]\n@end\n"
        formatted = cli._format_clpy(messy, _openers())
        run_source(formatted)
        assert capsys.readouterr().out.strip().splitlines() == ["0", "1"]

    def test_namespaced_plugin_block_indented(self):
        from cruhon.core.lexer import get_lexer
        src = (
            "@discord.command[ping; ctx]\n"
            "@discord.reply[ctx; \"pong\"]\n"
            "@end\n"
        )
        out = cli._format_clpy(src, _openers(), lexer=get_lexer())
        lines = out.splitlines()
        assert lines[0] == "@discord.command[ping; ctx]"
        assert lines[1] == "    @discord.reply[ctx; \"pong\"]"
        assert lines[2] == "@end"

    def test_raw_body_left_verbatim(self):
        src = (
            "@raw\n"
            "      x = [i for i in range(3)]\n"
            "@end\n"
        )
        out = cli._format_clpy(src, _openers())
        # body line keeps its original (Python) indentation, not Cruhon's
        assert "      x = [i for i in range(3)]" in out


# ─────────────────────────────────────────────────────────────
# repl — _repl_eval
# ─────────────────────────────────────────────────────────────

class TestReplEval:
    def _ns(self):
        return {"__name__": "__main__"}

    def test_statement_executes(self, capsys):
        ns = self._ns()
        cli._repl_eval("@var[x; 7]", ns, parse, transpile)
        cli._repl_eval("@print[{x}]", ns, parse, transpile)
        assert capsys.readouterr().out.strip() == "7"

    def test_definitions_persist(self, capsys):
        ns = self._ns()
        cli._repl_eval(
            "@func[double; n]\n    @return[n * 2]\n@end",
            ns, parse, transpile,
        )
        cli._repl_eval("@print[{double(5)}]", ns, parse, transpile)
        assert capsys.readouterr().out.strip() == "10"

    def test_bare_expression_echoes_value(self, capsys):
        ns = self._ns()
        # @math.sqrt transpiles to a self-contained __import__('math').sqrt(...)
        cli._repl_eval("@math.sqrt[16]", ns, parse, transpile)
        out = capsys.readouterr().out
        assert "=>" in out and "4.0" in out

    def test_syntax_error_is_reported_not_raised(self, capsys):
        ns = self._ns()
        cli._repl_eval("@for[", ns, parse, transpile)  # malformed
        assert "✗" in capsys.readouterr().out


# ─────────────────────────────────────────────────────────────
# docs / repl block-opener discovery
# ─────────────────────────────────────────────────────────────

class TestOpeners:
    def test_core_block_openers_present(self):
        openers = _openers()
        for kw in ("for", "while", "if", "func", "class", "try", "with"):
            assert kw in openers

    def test_decorator_excluded(self):
        assert "decorator" not in _openers()

    def test_plugin_block_commands_included(self):
        # Plugin blocks are registered under their internal (lexer-rewritten)
        # names, e.g. discord's @discord.on -> _dc_on.
        openers = _openers()
        assert "_dc_on" in openers

    def test_namespaced_plugin_block_resolves_via_lexer(self):
        # @discord.on[...] in source must resolve to a registered opener after
        # the discord lexer pre-hook rewrites it.
        from cruhon.core.lexer import get_lexer
        cmd = cli._effective_leading_cmd("@discord.on[member]", get_lexer())
        assert cmd == "_dc_on"
        assert cmd in _openers()


class TestDocsCommand:
    def test_docs_list_runs(self, capsys):
        class A:
            plugin = None
        cli.cmd_docs(A())
        out = capsys.readouterr().out
        assert "Plugins with docs" in out

    def test_docs_specific_plugin(self, capsys):
        class A:
            plugin = "discord"
        cli.cmd_docs(A())
        out = capsys.readouterr().out
        assert "cruhon-discord" in out

    def test_docs_unknown_plugin_exits(self, capsys):
        class A:
            plugin = "does_not_exist_xyz"
        with pytest.raises(SystemExit):
            cli.cmd_docs(A())
