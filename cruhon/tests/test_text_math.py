"""
Tests for Text & I/O and Math & Numbers namespaces:
@textwrap, @getpass, @cmath, @array
"""
import cmath
import math

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
# @textwrap
# ─────────────────────────────────────────────────────────────

class TestTextwrap:
    def test_wrap_default(self):
        g = run('@var[r; @textwrap.wrap["hello world this is a test"]]')
        assert g["r"] == ["hello world this is a test"]

    def test_wrap_width(self):
        g = run('@var[r; @textwrap.wrap["aaaa bbbb cccc"; 9]]')
        assert g["r"] == ["aaaa bbbb", "cccc"]

    def test_fill_default(self):
        g = run('@var[r; @textwrap.fill["hello world"]]')
        assert g["r"] == "hello world"

    def test_fill_width(self):
        g = run('@var[r; @textwrap.fill["aaaa bbbb cccc"; 9]]')
        assert g["r"] == "aaaa bbbb\ncccc"

    def test_shorten(self):
        g = run('@var[r; @textwrap.shorten["hello world foo bar"; 12]]')
        assert g["r"] == "hello [...]"

    def test_indent(self):
        g = run('@var[r; @textwrap.indent["a\\nb"; "> "]]')
        assert g["r"] == "> a\n> b"

    def test_dedent(self):
        g = run('@var[r; @textwrap.dedent["    a\\n    b"]]')
        assert g["r"] == "a\nb"

    def test_center(self):
        g = run('@var[r; @textwrap.center["hi"; 6]]')
        assert g["r"] == "  hi  "

    def test_truncate_short(self):
        g = run('@var[r; @textwrap.truncate["hi"; 5]]')
        assert g["r"] == "hi"

    def test_truncate_long(self):
        g = run('@var[r; @textwrap.truncate["hello world"; 5]]')
        assert g["r"] == "hello…"


# ─────────────────────────────────────────────────────────────
# @getpass
# ─────────────────────────────────────────────────────────────

class TestGetpass:
    def test_user(self):
        import getpass
        g = run('@var[u; @getpass.user[]]')
        assert g["u"] == getpass.getuser()

    def test_ask_monkeypatched(self, monkeypatch):
        import getpass
        monkeypatch.setattr(getpass, "getpass", lambda *a: "secret")
        g = run('@var[p; @getpass.ask["Pwd: "]]')
        assert g["p"] == "secret"

    def test_password_alias(self, monkeypatch):
        import getpass
        monkeypatch.setattr(getpass, "getpass", lambda *a: "hunter2")
        g = run('@var[p; @getpass.password[]]')
        assert g["p"] == "hunter2"


# ─────────────────────────────────────────────────────────────
# @cmath
# ─────────────────────────────────────────────────────────────

class TestCmath:
    def test_complex(self):
        g = run('@var[z; @cmath.complex[3; 4]]')
        assert g["z"] == complex(3, 4)

    def test_modulus(self):
        g = run('@var[m; @cmath.modulus[@cmath.complex[3; 4]]]')
        assert g["m"] == 5.0

    def test_phase(self):
        g = run('@var[p; @cmath.phase[@cmath.complex[0; 1]]]')
        assert math.isclose(g["p"], math.pi / 2)

    def test_polar(self):
        g = run('@var[p; @cmath.polar[@cmath.complex[1; 0]]]')
        assert g["p"] == (1.0, 0.0)

    def test_rect(self):
        g = run('@var[z; @cmath.rect[1; 0]]')
        assert math.isclose(g["z"].real, 1.0)

    def test_conjugate(self):
        g = run('@var[z; @cmath.conjugate[@cmath.complex[2; 3]]]')
        assert g["z"] == complex(2, -3)

    def test_sqrt_negative(self):
        g = run('@var[z; @cmath.sqrt[-1]]')
        assert g["z"] == complex(0, 1)

    def test_exp(self):
        g = run('@var[z; @cmath.exp[0]]')
        assert g["z"] == complex(1, 0)

    def test_log(self):
        g = run('@var[z; @cmath.log[@cmath.exp[1]]]')
        assert math.isclose(g["z"].real, 1.0, abs_tol=1e-9)

    def test_log_base(self):
        g = run('@var[z; @cmath.log[8; 2]]')
        assert math.isclose(g["z"].real, 3.0, abs_tol=1e-9)

    def test_sin(self):
        g = run('@var[z; @cmath.sin[0]]')
        assert g["z"] == complex(0, 0)

    def test_is_nan(self):
        g = run('@var[b; @cmath.is_nan[@cmath.nan[]]]')
        assert g["b"] is True

    def test_is_finite(self):
        g = run('@var[b; @cmath.is_finite[@cmath.complex[1; 1]]]')
        assert g["b"] is True

    def test_is_close(self):
        g = run('@var[b; @cmath.is_close[1.0; 1.0]]')
        assert g["b"] is True

    def test_pi(self):
        g = run('@var[p; @cmath.pi[]]')
        assert g["p"] == cmath.pi


# ─────────────────────────────────────────────────────────────
# @array
# ─────────────────────────────────────────────────────────────

class TestArray:
    def test_of_empty(self):
        g = run('@var[a; @array.of["i"]]')
        assert list(g["a"]) == []

    def test_of_filled(self):
        g = run('@var[a; @array.of["i"; [1, 2, 3]]]')
        assert list(g["a"]) == [1, 2, 3]

    def test_zeros(self):
        g = run('@var[a; @array.zeros["i"; 4]]')
        assert list(g["a"]) == [0, 0, 0, 0]

    def test_range(self):
        g = run('@var[a; @array.range["i"; 3]]')
        assert list(g["a"]) == [0, 1, 2]

    def test_to_bytes_roundtrip(self):
        g = run('@var[b; @array.to_bytes[@array.of["i"; [1, 2]]]]')
        assert isinstance(g["b"], bytes)

    def test_from_bytes(self):
        src = '@var[b; @array.to_bytes[@array.of["i"; [7, 8]]]]\n@var[a; @array.from_bytes["i"; b]]'
        g = run(src)
        assert list(g["a"]) == [7, 8]

    def test_to_list(self):
        g = run('@var[l; @array.to_list[@array.of["i"; [4, 5]]]]')
        assert g["l"] == [4, 5]

    def test_item_size(self):
        g = run('@var[s; @array.item_size[@array.of["d"; [1.0]]]]')
        assert g["s"] == 8

    def test_typecode(self):
        g = run('@var[t; @array.typecode[@array.of["i"]]]')
        assert g["t"] == "i"

    def test_length(self):
        g = run('@var[n; @array.length[@array.of["i"; [1, 2, 3]]]]')
        assert g["n"] == 3

    def test_sum(self):
        g = run('@var[s; @array.sum[@array.of["i"; [1, 2, 3]]]]')
        assert g["s"] == 6

    def test_min_max(self):
        g = run('@var[lo; @array.min[@array.of["i"; [3, 1, 2]]]]\n@var[hi; @array.max[@array.of["i"; [3, 1, 2]]]]')
        assert g["lo"] == 1 and g["hi"] == 3
