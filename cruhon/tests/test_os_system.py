"""
Tests for OS & System (system/config) namespaces:
@signal, @mmap, @atexit, @locale, @gettext, @argparse, @sysconfig, @resource
"""
import signal as _signal
import sys
import sysconfig as _sysconfig

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
# @signal
# ─────────────────────────────────────────────────────────────

class TestSignal:
    def test_number(self):
        g = run('@var[n; @signal.number["SIGINT"]]')
        assert g["n"] == int(_signal.SIGINT)

    def test_name(self):
        g = run(f'@var[s; @signal.name[{int(_signal.SIGINT)}]]')
        assert g["s"] == "SIGINT"

    def test_describe(self):
        g = run(f'@var[s; @signal.describe[{int(_signal.SIGINT)}]]')
        assert isinstance(g["s"], str)

    def test_valid(self):
        g = run('@var[v; @signal.valid[]]')
        assert int(_signal.SIGINT) in g["v"]

    def test_get(self):
        g = run(f'@var[h; @signal.get[{int(_signal.SIGINT)}]]')
        assert g["h"] is not None


# ─────────────────────────────────────────────────────────────
# @mmap
# ─────────────────────────────────────────────────────────────

class TestMmap:
    def _file(self, tmp_path):
        p = tmp_path / "data.bin"
        p.write_bytes(b"hello world hello")
        return p

    def test_read(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[b; @mmap.read["{p}"]]')
        assert g["b"] == b"hello world hello"

    def test_size(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[n; @mmap.size["{p}"]]')
        assert g["n"] == 17

    def test_slice(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[b; @mmap.slice["{p}"; 0; 5]]')
        assert g["b"] == b"hello"

    def test_find(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[i; @mmap.find["{p}"; b"world"]]')
        assert g["i"] == 6

    def test_contains(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[b; @mmap.contains["{p}"; b"world"]]')
        assert g["b"] is True

    def test_count(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[n; @mmap.count["{p}"; b"hello"]]')
        assert g["n"] == 2


# ─────────────────────────────────────────────────────────────
# @atexit
# ─────────────────────────────────────────────────────────────

class TestAtexit:
    def test_register_unregister(self):
        import atexit
        calls = []

        def cb():
            calls.append(1)

        g = run('@var[f; @atexit.register[cb]]', {"cb": cb})
        assert g["f"] is cb
        run('@atexit.unregister[cb]', {"cb": cb})
        # after unregister, running exit funcs should not call it
        atexit._run_exitfuncs()
        assert calls == []


# ─────────────────────────────────────────────────────────────
# @locale
# ─────────────────────────────────────────────────────────────

class TestLocale:
    def test_set_and_get(self):
        run('@locale.set["C"]')
        g = run('@var[loc; @locale.get[]]')
        assert isinstance(g["loc"], tuple)

    def test_number(self):
        run('@locale.set["C"]')
        g = run('@var[s; @locale.number[1000]]')
        assert g["s"] == "1000"

    def test_atof(self):
        run('@locale.set["C"]')
        g = run('@var[f; @locale.atof["3.5"]]')
        assert g["f"] == 3.5

    def test_encoding(self):
        g = run('@var[e; @locale.encoding[]]')
        assert isinstance(g["e"], str)


# ─────────────────────────────────────────────────────────────
# @gettext
# ─────────────────────────────────────────────────────────────

class TestGettext:
    def test_passthrough(self):
        g = run('@var[s; @gettext.t["Hello"]]')
        assert g["s"] == "Hello"

    def test_plural_singular(self):
        g = run('@var[s; @gettext.plural["1 item"; "n items"; 1]]')
        assert g["s"] == "1 item"

    def test_plural_many(self):
        g = run('@var[s; @gettext.plural["1 item"; "n items"; 5]]')
        assert g["s"] == "n items"


# ─────────────────────────────────────────────────────────────
# @argparse
# ─────────────────────────────────────────────────────────────

class TestArgparse:
    def test_parse_flag(self):
        g = run('@var[ns; @argparse.parse[["--name"]; ["--name", "bob"]]]')
        assert g["ns"].name == "bob"

    def test_parse_dict(self):
        g = run('@var[d; @argparse.parse_dict[["--name"]; ["--name", "x"]]]')
        assert g["d"] == {"name": "x"}

    def test_parse_with_options(self):
        src = '@var[d; @argparse.parse_dict[[["--n", {"type": int}]]; ["--n", "7"]]]'
        g = run(src)
        assert g["d"] == {"n": 7}

    def test_new(self):
        import argparse
        g = run('@var[p; @argparse.new["my tool"]]')
        assert isinstance(g["p"], argparse.ArgumentParser)
        assert g["p"].description == "my tool"

    def test_to_dict(self):
        import argparse
        ns = argparse.Namespace(a=1, b=2)
        g = run('@var[d; @argparse.to_dict[ns]]', {"ns": ns})
        assert g["d"] == {"a": 1, "b": 2}


# ─────────────────────────────────────────────────────────────
# @sysconfig
# ─────────────────────────────────────────────────────────────

class TestSysconfig:
    def test_paths(self):
        g = run('@var[p; @sysconfig.paths[]]')
        assert isinstance(g["p"], dict) and "purelib" in g["p"]

    def test_path(self):
        g = run('@var[p; @sysconfig.path["purelib"]]')
        assert g["p"] == _sysconfig.get_path("purelib")

    def test_platform(self):
        g = run('@var[p; @sysconfig.platform[]]')
        assert g["p"] == _sysconfig.get_platform()

    def test_version(self):
        g = run('@var[v; @sysconfig.version[]]')
        assert g["v"] == _sysconfig.get_python_version()

    def test_var(self):
        g = run('@var[v; @sysconfig.var["EXT_SUFFIX"]]')
        assert g["v"] == _sysconfig.get_config_var("EXT_SUFFIX")


# ─────────────────────────────────────────────────────────────
# @resource
# ─────────────────────────────────────────────────────────────

@pytest.mark.skipif(sys.platform == "win32", reason="resource is Unix-only")
class TestResource:
    def test_usage(self):
        g = run('@var[u; @resource.usage[]]')
        assert hasattr(g["u"], "ru_maxrss")

    def test_max_rss(self):
        g = run('@var[m; @resource.max_rss[]]')
        assert isinstance(g["m"], int)

    def test_user_time(self):
        g = run('@var[t; @resource.user_time[]]')
        assert isinstance(g["t"], float)

    def test_limit(self):
        g = run('@var[l; @resource.limit["NOFILE"]]')
        assert isinstance(g["l"], tuple) and len(g["l"]) == 2

    def test_page_size(self):
        g = run('@var[p; @resource.page_size[]]')
        assert isinstance(g["p"], int) and g["p"] > 0
