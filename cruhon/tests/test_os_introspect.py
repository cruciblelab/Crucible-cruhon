"""
Tests for OS & System introspection namespaces:
@gc, @inspect, @traceback, @warnings, @weakref, @types, @abc
"""
import gc as _gc
import textwrap as _textwrap
import types as _types

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
# @gc
# ─────────────────────────────────────────────────────────────

class TestGc:
    def test_collect(self):
        g = run('@var[n; @gc.collect[]]')
        assert isinstance(g["n"], int)

    def test_is_enabled(self):
        g = run('@var[b; @gc.is_enabled[]]')
        assert isinstance(g["b"], bool)

    def test_count(self):
        g = run('@var[c; @gc.count[]]')
        assert isinstance(g["c"], tuple) and len(g["c"]) == 3

    def test_threshold(self):
        g = run('@var[t; @gc.threshold[]]')
        assert isinstance(g["t"], tuple)

    def test_is_tracked(self):
        g = run('@var[b; @gc.is_tracked[[1, 2, 3]]]')
        assert g["b"] is True

    def test_enable_disable_roundtrip(self):
        was = _gc.isenabled()
        run('@gc.enable[]')
        assert _gc.isenabled() is True
        if not was:
            _gc.disable()


# ─────────────────────────────────────────────────────────────
# @inspect
# ─────────────────────────────────────────────────────────────

class TestInspect:
    def test_source(self):
        g = run('@var[s; @inspect.source[fn]]', {"fn": _textwrap.shorten})
        assert "def shorten" in g["s"]

    def test_doc(self):
        g = run('@var[d; @inspect.doc[fn]]', {"fn": _textwrap.shorten})
        assert isinstance(g["d"], str) and len(g["d"]) > 0

    def test_signature(self):
        g = run('@var[s; @inspect.signature[fn]]', {"fn": _textwrap.shorten})
        assert g["s"].startswith("(")

    def test_parameters(self):
        g = run('@var[p; @inspect.parameters[fn]]', {"fn": _textwrap.shorten})
        assert "text" in g["p"] and "width" in g["p"]

    def test_is_function(self):
        g = run('@var[b; @inspect.is_function[fn]]', {"fn": _textwrap.shorten})
        assert g["b"] is True

    def test_is_class(self):
        g = run('@var[b; @inspect.is_class[c]]', {"c": dict})
        assert g["b"] is True

    def test_mro(self):
        g = run('@var[m; @inspect.mro[c]]', {"c": bool})
        assert int in g["m"]


# ─────────────────────────────────────────────────────────────
# @traceback
# ─────────────────────────────────────────────────────────────

class TestTraceback:
    def test_format_exception(self):
        e = ValueError("boom")
        g = run('@var[s; @traceback.format_exception[e]]', {"e": e})
        assert "ValueError" in g["s"] and "boom" in g["s"]

    def test_message(self):
        e = TypeError("nope")
        g = run('@var[s; @traceback.message[e]]', {"e": e})
        assert g["s"] == "TypeError: nope"

    def test_stack(self):
        g = run('@var[s; @traceback.stack[]]')
        assert isinstance(g["s"], list)


# ─────────────────────────────────────────────────────────────
# @warnings
# ─────────────────────────────────────────────────────────────

class TestWarnings:
    def test_warn(self):
        with pytest.warns(UserWarning):
            run('@warnings.warn["hi"]')

    def test_deprecated(self):
        with pytest.warns(DeprecationWarning):
            run('@warnings.deprecated["old"]')

    def test_error_filter_raises(self):
        import warnings as _w
        with _w.catch_warnings():
            run('@warnings.error[]')
            with pytest.raises(UserWarning):
                run('@warnings.warn["bad"]')


# ─────────────────────────────────────────────────────────────
# @weakref
# ─────────────────────────────────────────────────────────────

class _Obj:
    pass


class TestWeakref:
    def test_ref_deref(self):
        o = _Obj()
        g = run('@var[r; @weakref.ref[o]]', {"o": o})
        assert g["r"]() is o

    def test_is_alive(self):
        o = _Obj()
        g = run('@var[r; @weakref.ref[o]]\n@var[b; @weakref.is_alive[r]]', {"o": o})
        assert g["b"] is True

    def test_count(self):
        o = _Obj()
        g = run('@var[r; @weakref.ref[o]]\n@var[n; @weakref.count[o]]', {"o": o})
        assert g["n"] == 1

    def test_dict(self):
        import weakref
        g = run('@var[d; @weakref.dict[]]')
        assert isinstance(g["d"], weakref.WeakValueDictionary)


# ─────────────────────────────────────────────────────────────
# @types
# ─────────────────────────────────────────────────────────────

class TestTypes:
    def test_namespace_empty(self):
        g = run('@var[n; @types.namespace[]]')
        assert isinstance(g["n"], _types.SimpleNamespace)

    def test_namespace_from_dict(self):
        g = run('@var[n; @types.namespace[{"x": 1}]]')
        assert g["n"].x == 1

    def test_readonly(self):
        g = run('@var[m; @types.readonly[{"a": 1}]]')
        assert g["m"]["a"] == 1
        with pytest.raises(TypeError):
            g["m"]["a"] = 2

    def test_is_function(self):
        g = run('@var[b; @types.is_function[fn]]', {"fn": _textwrap.shorten})
        assert g["b"] is True

    def test_is_lambda(self):
        g = run('@var[b; @types.is_lambda[fn]]', {"fn": lambda: 1})
        assert g["b"] is True


# ─────────────────────────────────────────────────────────────
# @abc
# ─────────────────────────────────────────────────────────────

class TestAbc:
    def test_is_abstract(self):
        from collections.abc import Mapping
        g = run('@var[b; @abc.is_abstract[c]]', {"c": Mapping})
        assert g["b"] is True

    def test_abstract_methods(self):
        from collections.abc import Sized
        g = run('@var[m; @abc.abstract_methods[c]]', {"c": Sized})
        assert "__len__" in g["m"]

    def test_is_subclass(self):
        from collections.abc import Sequence
        g = run('@var[b; @abc.is_subclass[base; c]]', {"base": Sequence, "c": list})
        assert g["b"] is True

    def test_register(self):
        from collections.abc import Hashable

        class _Custom:
            pass

        g = run('@var[c; @abc.register[base; cls]]\n@var[b; @abc.is_subclass[base; cls]]',
                {"base": Hashable, "cls": _Custom})
        assert g["b"] is True
