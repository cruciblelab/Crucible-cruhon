"""
Tests for file management and utility namespaces:
@shutil, @filecmp, @configparser, @errno, @linecache, @numbers
"""
import errno as _errno
import os
import textwrap

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
# @shutil
# ─────────────────────────────────────────────────────────────

class TestShutil:
    def test_copy(self, tmp_path):
        src = tmp_path / "a.txt"
        dst = tmp_path / "b.txt"
        src.write_text("hello")
        run(f'@shutil.copy["{src}"; "{dst}"]')
        assert dst.read_text(encoding="utf-8") == "hello"

    def test_move(self, tmp_path):
        src = tmp_path / "c.txt"
        dst = tmp_path / "d.txt"
        src.write_text("move me")
        run(f'@shutil.move["{src}"; "{dst}"]')
        assert dst.read_text(encoding="utf-8") == "move me" and not src.exists()

    def test_rmtree(self, tmp_path):
        d = tmp_path / "sub"
        d.mkdir()
        (d / "f.txt").write_text("x")
        run(f'@shutil.rmtree["{d}"]')
        assert not d.exists()

    def test_copy_tree(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "x.txt").write_text("y")
        dst = tmp_path / "dst"
        run(f'@shutil.copy_tree["{src}"; "{dst}"]')
        assert (dst / "x.txt").read_text(encoding="utf-8") == "y"

    def test_disk_usage(self, tmp_path):
        g = run(f'@var[u; @shutil.disk_usage["{tmp_path}"]]')
        assert g["u"].total > 0

    def test_free(self, tmp_path):
        g = run(f'@var[f; @shutil.free["{tmp_path}"]]')
        assert isinstance(g["f"], int) and g["f"] >= 0

    def test_which(self):
        g = run('@var[p; @shutil.which["python3"]]')
        assert g["p"] is not None and "python" in g["p"]


# ─────────────────────────────────────────────────────────────
# @filecmp
# ─────────────────────────────────────────────────────────────

class TestFilecmp:
    def test_equal_same(self, tmp_path):
        (tmp_path / "a.txt").write_text("x")
        (tmp_path / "b.txt").write_text("x")
        g = run(f'@var[b; @filecmp.equal["{tmp_path}/a.txt"; "{tmp_path}/b.txt"]]')
        assert g["b"] is True

    def test_equal_different(self, tmp_path):
        (tmp_path / "a.txt").write_text("x")
        (tmp_path / "b.txt").write_text("y")
        g = run(f'@var[b; @filecmp.equal["{tmp_path}/a.txt"; "{tmp_path}/b.txt"]]')
        assert g["b"] is False

    def test_same_files(self, tmp_path):
        d1, d2 = tmp_path / "d1", tmp_path / "d2"
        d1.mkdir(); d2.mkdir()
        (d1 / "same.txt").write_text("hi")
        (d2 / "same.txt").write_text("hi")
        (d1 / "only1.txt").write_text("a")
        g = run(f'@var[s; @filecmp.same_files["{d1}"; "{d2}"]]')
        assert "same.txt" in g["s"]

    def test_left_only(self, tmp_path):
        d1, d2 = tmp_path / "d1", tmp_path / "d2"
        d1.mkdir(); d2.mkdir()
        (d1 / "only1.txt").write_text("a")
        g = run(f'@var[s; @filecmp.left_only["{d1}"; "{d2}"]]')
        assert "only1.txt" in g["s"]


# ─────────────────────────────────────────────────────────────
# @configparser
# ─────────────────────────────────────────────────────────────

class TestConfigparser:
    _INI = textwrap.dedent("""\
        [server]
        host = localhost
        port = 8080
        debug = true
        weight = 1.5
    """)

    def test_loads_get(self):
        g = run('@var[c; @configparser.loads[ini]]\n@var[v; @configparser.get[c; "server"; "host"]]',
                {"ini": self._INI})
        assert g["v"] == "localhost"

    def test_getint(self):
        g = run('@var[c; @configparser.loads[ini]]\n@var[v; @configparser.getint[c; "server"; "port"]]',
                {"ini": self._INI})
        assert g["v"] == 8080

    def test_getfloat(self):
        g = run('@var[c; @configparser.loads[ini]]\n@var[v; @configparser.getfloat[c; "server"; "weight"]]',
                {"ini": self._INI})
        assert g["v"] == 1.5

    def test_getbool(self):
        g = run('@var[c; @configparser.loads[ini]]\n@var[v; @configparser.getbool[c; "server"; "debug"]]',
                {"ini": self._INI})
        assert g["v"] is True

    def test_sections(self):
        g = run('@var[c; @configparser.loads[ini]]\n@var[s; @configparser.sections[c]]',
                {"ini": self._INI})
        assert g["s"] == ["server"]

    def test_set_and_dumps(self):
        src = (
            '@var[c; @configparser.new[]]\n'
            '@configparser.add_section[c; "x"]\n'
            '@configparser.set[c; "x"; "k"; "v"]\n'
            '@var[s; @configparser.dumps[c]]'
        )
        g = run(src)
        assert "[x]" in g["s"] and "k = v" in g["s"]

    def test_has(self):
        g = run('@var[c; @configparser.loads[ini]]\n@var[b; @configparser.has[c; "server"; "host"]]',
                {"ini": self._INI})
        assert g["b"] is True

    def test_save_and_load(self, tmp_path):
        p = tmp_path / "test.ini"
        src = (
            f'@var[c; @configparser.new[]]\n'
            f'@configparser.add_section[c; "s"]\n'
            f'@configparser.set[c; "s"; "a"; "1"]\n'
            f'@configparser.save[c; "{p}"]\n'
            f'@var[c2; @configparser.load["{p}"]]\n'
            f'@var[v; @configparser.get[c2; "s"; "a"]]'
        )
        g = run(src)
        assert g["v"] == "1"


# ─────────────────────────────────────────────────────────────
# @errno
# ─────────────────────────────────────────────────────────────

class TestErrno:
    def test_name(self):
        g = run(f'@var[s; @errno.name[{_errno.ENOENT}]]')
        assert g["s"] == "ENOENT"

    def test_description(self):
        g = run(f'@var[s; @errno.description[{_errno.ENOENT}]]')
        assert isinstance(g["s"], str) and len(g["s"]) > 0

    def test_code(self):
        g = run('@var[n; @errno.code["ENOENT"]]')
        assert g["n"] == _errno.ENOENT

    def test_ENOENT(self):
        g = run('@var[n; @errno.ENOENT[]]')
        assert g["n"] == _errno.ENOENT

    def test_all(self):
        g = run('@var[d; @errno.all[]]')
        assert isinstance(g["d"], dict) and _errno.ENOENT in g["d"]


# ─────────────────────────────────────────────────────────────
# @linecache
# ─────────────────────────────────────────────────────────────

class TestLinecache:
    def test_lines(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_text("a\nb\nc\n")
        g = run(f'@var[l; @linecache.lines["{p}"]]')
        assert g["l"] == ["a\n", "b\n", "c\n"]

    def test_line(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_text("hello\nworld\n")
        g = run(f'@var[s; @linecache.line["{p}"; 2]]')
        assert g["s"] == "world\n"

    def test_clear(self):
        run('@linecache.clear[]')


# ─────────────────────────────────────────────────────────────
# @numbers
# ─────────────────────────────────────────────────────────────

class TestNumbers:
    def test_is_number_int(self):
        g = run('@var[b; @numbers.is_number[42]]')
        assert g["b"] is True

    def test_is_number_str(self):
        g = run('@var[b; @numbers.is_number["hi"]]')
        assert g["b"] is False

    def test_is_real(self):
        g = run('@var[b; @numbers.is_real[3.14]]')
        assert g["b"] is True

    def test_is_integral(self):
        g = run('@var[b; @numbers.is_integral[5]]')
        assert g["b"] is True

    def test_is_integral_float(self):
        g = run('@var[b; @numbers.is_integral[5.0]]')
        assert g["b"] is False
