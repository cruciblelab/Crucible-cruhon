"""
Regression test for a real parser bug: plugin commands registered with a
"." in their name (api.command("ns.method", ...) / api.block_command(
"ns.method", ...)) were completely unreachable via @ns.method[...] syntax.

The lexer always splits "ns.method" into NAMESPACE + DOT + AT_CMD tokens,
and _parse_statement()'s NAMESPACE branch went straight to
_parse_namespace_call() (treating it as a stdlib/mod namespace method
call) without ever checking self._block_commands / self._commands for a
matching dotted registration — silently producing wrong code (or, worse,
colliding with an existing stdlib namespace of the same prefix) instead
of routing to the plugin's own visitor.

Discovered while auditing the README's "Complete Plugin Example" against
the real compiler — it demonstrated exactly this broken pattern
(api.block_command("log.timed", ...) invoked as @log.timed[...] ... @end).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core.mod_loader import ModAPI
from cruhon.core.parser import get_parser
from cruhon.core.transpiler import get_transpiler
from cruhon.core.runner import run_source


def _fresh_api(mod_name="test-dotted-mod"):
    return ModAPI(mod_name)


class TestDottedBlockCommand:
    def test_registers_and_dispatches(self):
        calls = []

        def visit_timed(transpiler, node):
            label = node.args[0] if node.args else '"block"'
            calls.append(label)
            body = "\n".join(r for n in node.body if (r := n.accept(transpiler)))
            return body or transpiler._line("pass")

        api = _fresh_api()
        api.block_command("zzztest.timed", visit_timed)

        src = '''@zzztest.timed["hello"]
    @var[x; 1]
@end'''
        code = get_transpiler().transpile(get_parser().parse(src))
        assert "x = 1" in code
        assert calls == ['"hello"']

    def test_body_is_not_dropped(self):
        """Before the fix, the indented body was silently orphaned."""
        hits = []

        def visit_timed(transpiler, node):
            hits.append(len(node.body))
            body = "\n".join(r for n in node.body if (r := n.accept(transpiler)))
            return body

        api = _fresh_api("test-dotted-mod-2")
        api.block_command("zzzbody.run", visit_timed)

        src = '''@zzzbody.run["x"]
    @var[a; 1]
    @var[b; 2]
    @var[c; 3]
@end'''
        code = get_transpiler().transpile(get_parser().parse(src))
        assert hits == [3]
        assert "a = 1" in code and "b = 2" in code and "c = 3" in code

    def test_end_to_end_execution(self):
        """Full run_source() path: parse → transpile → exec."""
        api = _fresh_api("test-dotted-mod-3")
        log = []
        api.inject("sink", lambda: log)

        def visit_capture(transpiler, node):
            label = node.args[0] if node.args else '"x"'
            body = "\n".join(r for n in node.body if (r := n.accept(transpiler)))
            return "\n".join([
                transpiler._line(f'sink.append({label})'),
                body or transpiler._line("pass"),
            ])

        api.block_command("capture.now", visit_capture)

        src = '''@capture.now["marker"]
    @var[computed; 2 + 2]
@end'''
        run_source(src)
        assert log == ["marker"]

    def test_dotted_command_beats_stdlib_namespace_collision(self):
        """
        A custom plugin registering a dotted name that happens to share
        its prefix with an existing stdlib namespace (e.g. "log") must
        still be reachable — the plugin registration takes priority over
        stdlib namespace dispatch for that exact dotted combination.
        Every OTHER method under that stdlib namespace is untouched.
        """
        api = _fresh_api("test-dotted-mod-4")
        hits = []

        def visit_special(transpiler, node):
            hits.append("dispatched")
            return transpiler._line("pass")

        # "log" is a real stdlib namespace (@log.setup, @log.info, ...).
        # "log.special_marker" is NOT one of its real methods.
        api.block_command("log.special_marker", visit_special)

        src = '''@log.special_marker["x"]
@end'''
        get_transpiler().transpile(get_parser().parse(src))
        assert hits == ["dispatched"]

        # A genuine stdlib @log.* call must still resolve normally.
        from cruhon.core.transpiler import Transpiler
        from cruhon.core.parser import Parser
        code = Transpiler().transpile(Parser().parse('@log.info["still works"]'))
        assert "logging" in code or "info" in code

    def test_non_block_dotted_command(self):
        """api.command("ns.method", ..., block=False) with a dotted name.

        api.command() auto-derives the expected AST node class name as
        f"{name.replace('.', '_').title()}Node" — for "zzzns.mark" that's
        "Zzzns_MarkNode" (Python's str.title() treats "_" as a word break).
        """
        from cruhon.core.ast_nodes import Node
        from dataclasses import dataclass

        @dataclass
        class Zzzns_MarkNode(Node):
            val: str = ""

        def parse_it(parser):
            parser.advance()
            args = parser.parse_args()
            return Zzzns_MarkNode(val=args[0] if args else '""', line=0)

        def visit_it(transpiler, node):
            return transpiler._line(f'RESULT.append({node.val})', node.line)

        api = _fresh_api("test-dotted-mod-5")
        api.command("zzzns.mark", parse_it, visit_it)

        code = get_transpiler().transpile(get_parser().parse('@zzzns.mark["hi"]'))
        assert 'RESULT.append("hi")' in code


class TestUnaffectedPaths:
    """Sanity: ordinary dotted namespace/mod calls are untouched."""

    def test_stdlib_namespace_call_unaffected(self):
        from cruhon.core.transpiler import Transpiler
        from cruhon.core.parser import Parser
        code = Transpiler().transpile(Parser().parse('@var[x; @math.sqrt[16]]'))
        assert "sqrt" in code

    def test_http_namespace_call_unaffected(self):
        from cruhon.core.transpiler import Transpiler
        from cruhon.core.parser import Parser
        code = Transpiler().transpile(Parser().parse('@var[r; @http.get["url"]]'))
        assert "requests.get" in code

    def test_yield_from_unaffected(self):
        from cruhon.core.transpiler import Transpiler
        from cruhon.core.parser import Parser
        src = '''@func[gen]
    @yield.from[range(3)]
@end'''
        code = Transpiler().transpile(Parser().parse(src))
        assert "yield from" in code

    def test_async_for_unaffected(self):
        from cruhon.core.transpiler import Transpiler
        from cruhon.core.parser import Parser
        src = '''@async[main]
    @async.for[item; gen()]
        @print[{item}]
    @end
@end'''
        code = Transpiler().transpile(Parser().parse(src))
        assert "async for" in code
