"""
Tests for v2.6.0 language features:
  @template/@render, @spread/@unpack, @let, @pipeline/@apply
"""
import pytest
from cruhon.core import parse, transpile
from cruhon.core.runner import run_source


def _t(src: str) -> str:
    return transpile(parse(src))


def _run(src: str):
    ns = {}
    code = _t(src)
    exec(compile(code, "<test>", "exec"), ns)
    return ns


def _eval(src: str):
    code = _t(f"@var[__r__; {src}]")
    ns = {}
    exec(compile(code, "<test>", "exec"), ns)
    return ns["__r__"]


# ─────────────────────────────────────────────────────────────
# @template / @render
# ─────────────────────────────────────────────────────────────

class TestTemplateNode:
    def test_template_transpiles(self):
        code = _t("@template[greeting]\n    Hello, {name}!\n@end")
        assert "__tmpl_greeting" in code
        assert "Hello" in code

    def test_template_render_inline(self):
        src = (
            "@template[tmpl]\n"
            "    Hi {x}\n"
            "@end\n"
            '@var[result; @render[tmpl; x="World"]]'
        )
        ns = _run(src)
        assert ns["result"] == "Hi World"

    def test_render_no_vars(self):
        src = (
            "@template[banner]\n"
            "    === BANNER ===\n"
            "@end\n"
            "@var[out; @render[banner]]"
        )
        ns = _run(src)
        assert ns["out"] == "=== BANNER ==="

    def test_render_multiple_vars(self):
        src = (
            "@template[msg]\n"
            "    {a} + {b} = {c}\n"
            "@end\n"
            "@var[out; @render[msg; a=1; b=2; c=3]]"
        )
        ns = _run(src)
        assert ns["out"] == "1 + 2 = 3"

    def test_template_multiline(self):
        src = (
            "@template[block]\n"
            "    line1\n"
            "    line2\n"
            "@end\n"
            "@var[out; @render[block]]"
        )
        ns = _run(src)
        assert "line1" in ns["out"]
        assert "line2" in ns["out"]

    def test_render_as_statement_transpiles(self):
        code = _t('@template[t]\n    hi\n@end\n@render[t]')
        assert "__tmpl_t" in code
        assert "format_map" in code

    def test_render_string_and_int_vars(self):
        src = (
            "@template[info]\n"
            "    name={name} age={age}\n"
            "@end\n"
            '@var[out; @render[info; name="Bob"; age=25]]'
        )
        ns = _run(src)
        assert ns["out"] == "name=Bob age=25"


# ─────────────────────────────────────────────────────────────
# @spread / @unpack
# ─────────────────────────────────────────────────────────────

class TestSpreadUnpack:
    def test_spread_transpiles(self):
        code = _t('@spread[print; ["a", "b"]]')
        assert "print(*" in code

    def test_unpack_transpiles(self):
        code = _t('@unpack[dict; {"a": 1}]')
        assert "dict(**" in code

    def test_spread_executes(self):
        src = "@var[nums; [3, 1, 2]]\n@var[result; @spread[max; nums]]"
        ns = _run(src)
        assert ns["result"] == 3

    def test_spread_inline(self):
        result = _eval("@spread[max; [5, 2, 8, 1]]")
        assert result == 8

    def test_unpack_inline(self):
        result = _eval('@unpack[dict; {"x": 10, "y": 20}]')
        assert result == {"x": 10, "y": 20}

    def test_spread_statement(self):
        src = "@var[out; []]\n@spread[out.extend; [[1, 2, 3]]]"
        ns = _run(src)
        assert ns["out"] == [1, 2, 3]

    def test_unpack_executes(self):
        src = "@var[kw; {\"x\": 10, \"y\": 20}]\n@var[result; @unpack[dict; kw]]"
        ns = _run(src)
        assert ns["result"] == {"x": 10, "y": 20}

    def test_spread_min_tuple(self):
        result = _eval("@spread[min; (7, 2, 9)]")
        assert result == 2

    def test_unpack_format(self):
        result = _eval('@unpack["{name} is {age}".format; {"name": "Ali", "age": 30}]')
        assert result == "Ali is 30"


# ─────────────────────────────────────────────────────────────
# @let
# ─────────────────────────────────────────────────────────────

class TestLetNode:
    def test_let_transpiles(self):
        code = _t("@let[x; 1; y; 2]")
        assert "x = 1" in code
        assert "y = 2" in code

    def test_let_executes(self):
        ns = _run("@let[a; 10; b; 20; c; 30]")
        assert ns["a"] == 10
        assert ns["b"] == 20
        assert ns["c"] == 30

    def test_let_single_pair(self):
        ns = _run("@let[x; 42]")
        assert ns["x"] == 42

    def test_let_odd_args_raises(self):
        with pytest.raises(Exception):
            _t("@let[x; 1; y]")

    def test_let_expression_values(self):
        ns = _run("@let[a; 2 + 2; b; 3 * 3]")
        assert ns["a"] == 4
        assert ns["b"] == 9

    def test_let_string_values(self):
        ns = _run('@let[first; "Alice"; last; "Smith"]')
        assert ns["first"] == "Alice"
        assert ns["last"] == "Smith"


# ─────────────────────────────────────────────────────────────
# @pipeline / @apply
# ─────────────────────────────────────────────────────────────

class TestPipelineApply:
    def test_pipeline_transpiles(self):
        code = _t("@pipeline[process; str.strip; str.upper]")
        assert "__pipeline_process" in code
        assert "lambda" in code

    def test_apply_transpiles(self):
        code = _t("@pipeline[p; str]\n@apply[p; 42]")
        assert "__pipeline_p(" in code

    def test_pipeline_executes(self):
        src = (
            "@pipeline[upcase; str.strip; str.upper]\n"
            '@var[result; @apply[upcase; "  hello  "]]'
        )
        ns = _run(src)
        assert ns["result"] == "HELLO"

    def test_pipeline_single_fn(self):
        ns = _run(
            "@pipeline[neg; lambda x: -x]\n"
            "@var[result; @apply[neg; 5]]"
        )
        assert ns["result"] == -5

    def test_pipeline_empty(self):
        ns = _run("@pipeline[id]\n@var[result; @apply[id; 42]]")
        assert ns["result"] == 42

    def test_pipeline_three_fns(self):
        src = (
            "@pipeline[proc; str.strip; str.lower; str.title]\n"
            '@var[result; @apply[proc; "  hELLO wORLD  "]]'
        )
        ns = _run(src)
        assert ns["result"] == "Hello World"

    def test_apply_inline(self):
        code = _t("@pipeline[neg; lambda x: -x]\n@var[r; @apply[neg; 10]]")
        assert "__pipeline_neg" in code

    def test_apply_statement(self):
        src = (
            "@var[out; []]\n"
            "@pipeline[push; lambda v: out.append(v)]\n"
            "@apply[push; 99]"
        )
        ns = _run(src)
        assert ns["out"] == [99]

    def test_pipeline_composition_order(self):
        src = (
            "@pipeline[p; lambda x: x + 1; lambda x: x * 2]\n"
            "@var[result; @apply[p; 3]]"
        )
        ns = _run(src)
        assert ns["result"] == 8  # (3+1)*2

    def test_pipeline_math(self):
        src = (
            "@pipeline[abs_neg; abs; lambda x: -x]\n"
            "@var[result; @apply[abs_neg; -5]]"
        )
        ns = _run(src)
        assert ns["result"] == -5  # abs(-5)=5, then -5
