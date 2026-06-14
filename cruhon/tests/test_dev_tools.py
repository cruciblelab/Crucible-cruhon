"""
Tests for Developer Tools and Other Utilities namespaces:
@ast, @dis, @keyword, @importlib, @graphlib, @reprlib, @tracemalloc
"""
import ast as _ast
import keyword as _keyword

import pytest

from cruhon.core.transpiler import Transpiler
from cruhon.core.parser import Parser


def transpile(src):
    return Transpiler().transpile(Parser().parse(src))


def run(src, globs=None):
    g = globs or {}
    exec(compile(transpile(src), "<test>", "exec"), g)
    return g


# ─────────────────────────────────────────────────────────────
# @ast
# ─────────────────────────────────────────────────────────────

class TestAst:
    def test_parse(self):
        g = run('@var[t; @ast.parse["x = 1"]]')
        assert isinstance(g["t"], _ast.Module)

    def test_dump(self):
        g = run('@var[s; @ast.dump["x = 1"]]')
        assert "Module" in g["s"] and "Assign" in g["s"]

    def test_literal(self):
        g = run('@var[v; @ast.literal["[1, 2, 3]"]]')
        assert g["v"] == [1, 2, 3]

    def test_unparse(self):
        node = _ast.parse("x = 1 + 2")
        g = run('@var[s; @ast.unparse[n]]', {"n": node})
        assert "x" in g["s"] and "1" in g["s"]

    def test_walk(self):
        g = run('@var[w; @ast.walk["x = 1 + 2"]]')
        assert any(type(n).__name__ == "BinOp" for n in g["w"])

    def test_node_types(self):
        g = run('@var[t; @ast.node_types["x = 1"]]')
        assert "Assign" in g["t"]

    def test_names(self):
        g = run('@var[n; @ast.names["x + y"]]')
        assert set(g["n"]) == {"x", "y"}


# ─────────────────────────────────────────────────────────────
# @dis
# ─────────────────────────────────────────────────────────────

def _sample():
    return 1 + 2


class TestDis:
    def test_disasm(self):
        g = run('@var[s; @dis.disasm[fn]]', {"fn": _sample})
        assert isinstance(g["s"], str) and len(g["s"]) > 0

    def test_instructions(self):
        import dis as _dis
        g = run('@var[i; @dis.instructions[fn]]', {"fn": _sample})
        assert isinstance(g["i"][0], _dis.Instruction)

    def test_opnames(self):
        g = run('@var[o; @dis.opnames[fn]]', {"fn": _sample})
        assert isinstance(g["o"], list) and all(isinstance(x, str) for x in g["o"])

    def test_consts(self):
        g = run('@var[c; @dis.consts[fn]]', {"fn": _sample})
        assert isinstance(g["c"], tuple)

    def test_code(self):
        g = run('@var[c; @dis.code[fn]]', {"fn": _sample})
        assert isinstance(g["c"], type(_sample.__code__))


# ─────────────────────────────────────────────────────────────
# @keyword
# ─────────────────────────────────────────────────────────────

class TestKeyword:
    def test_is_keyword_true(self):
        g = run('@var[b; @keyword.is_keyword["for"]]')
        assert g["b"] is True

    def test_is_keyword_false(self):
        g = run('@var[b; @keyword.is_keyword["foo"]]')
        assert g["b"] is False

    def test_all(self):
        g = run('@var[k; @keyword.all[]]')
        assert "for" in g["k"] and "while" in g["k"]

    def test_count(self):
        g = run('@var[n; @keyword.count[]]')
        assert g["n"] == len(_keyword.kwlist)

    def test_is_soft(self):
        g = run('@var[b; @keyword.is_soft["match"]]')
        assert isinstance(g["b"], bool)


# ─────────────────────────────────────────────────────────────
# @importlib
# ─────────────────────────────────────────────────────────────

class TestImportlib:
    def test_load(self):
        import json
        g = run('@var[m; @importlib.load["json"]]')
        assert g["m"] is json

    def test_attr(self):
        g = run('@var[f; @importlib.attr["json"; "dumps"]]')
        import json
        assert g["f"] is json.dumps

    def test_reload(self):
        import json
        g = run('@var[m; @importlib.reload[mod]]', {"mod": json})
        import json as _json2
        assert g["m"].__name__ == "json"

    def test_spec(self):
        import importlib.util
        g = run('@var[s; @importlib.spec["json"]]')
        assert g["s"].name == "json"

    def test_origin(self):
        g = run('@var[p; @importlib.origin["json"]]')
        assert g["p"] is not None and "json" in g["p"]


# ─────────────────────────────────────────────────────────────
# @graphlib
# ─────────────────────────────────────────────────────────────

class TestGraphlib:
    def test_sort_simple(self):
        g = run('@var[r; @graphlib.sort[{"b": {"a"}, "c": {"b"}}]]')
        assert g["r"].index("a") < g["r"].index("b") < g["r"].index("c")

    def test_sort_empty(self):
        g = run('@var[r; @graphlib.sort[{}]]')
        assert g["r"] == []

    def test_is_dag_true(self):
        g = run('@var[b; @graphlib.is_dag[{"b": {"a"}}]]')
        assert g["b"] is True

    def test_sort_independent(self):
        g = run('@var[r; @graphlib.sort[{"a": {}, "b": {}}]]')
        assert set(g["r"]) == {"a", "b"}


# ─────────────────────────────────────────────────────────────
# @reprlib
# ─────────────────────────────────────────────────────────────

class TestReprlib:
    def test_repr_large_list(self):
        big = list(range(1000))
        g = run('@var[s; @reprlib.repr[big]]', {"big": big})
        assert "..." in g["s"]

    def test_repr_short_list(self):
        g = run('@var[s; @reprlib.repr[[1, 2]]]')
        assert g["s"] == "[1, 2]"

    def test_short(self):
        g = run('@var[s; @reprlib.short["hello world this is long"]]')
        assert "..." in g["s"]


# ─────────────────────────────────────────────────────────────
# @tracemalloc
# ─────────────────────────────────────────────────────────────

class TestTracemalloc:
    def test_start_stop(self):
        g = run('@tracemalloc.start[]\n@var[b; @tracemalloc.is_tracing[]]\n@tracemalloc.stop[]')
        assert g["b"] is True

    def test_current(self):
        run('@tracemalloc.start[]')
        g = run('@var[c; @tracemalloc.current[]]')
        run('@tracemalloc.stop[]')
        cur, peak = g["c"]
        assert isinstance(cur, int) and isinstance(peak, int)

    def test_snapshot_top(self):
        run('@tracemalloc.start[]')
        data = [0] * 100000
        g = run('@var[t; @tracemalloc.top[3]]')
        run('@tracemalloc.stop[]')
        assert isinstance(g["t"], list) and len(g["t"]) <= 3
