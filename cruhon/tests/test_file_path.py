"""
Tests for File & Path namespaces: @glob, @tempfile, @fnmatch, @fileinput, @stat
"""
import os
import stat as _stat
from pathlib import Path

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
# @glob
# ─────────────────────────────────────────────────────────────

class TestGlob:
    def _setup(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        (tmp_path / "c.py").write_text("c")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "d.txt").write_text("d")
        (sub / "e.py").write_text("e")
        return tmp_path

    def test_glob_basic(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[m; @glob.glob["{tmp_path}/*.txt"]]'
        g = run(src)
        assert len(g["m"]) == 2

    def test_rglob(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[m; @glob.rglob["{tmp_path}"; "*.txt"]]'
        g = run(src)
        assert len(g["m"]) == 3

    def test_files(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[fs; @glob.files["{tmp_path}"]]'
        g = run(src)
        assert len(g["fs"]) == 3

    def test_files_pattern(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[fs; @glob.files["{tmp_path}"; "*.txt"]]'
        g = run(src)
        assert len(g["fs"]) == 2

    def test_files_r(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[fs; @glob.files_r["{tmp_path}"]]'
        g = run(src)
        assert len(g["fs"]) == 5

    def test_files_r_pattern(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[fs; @glob.files_r["{tmp_path}"; "*.py"]]'
        g = run(src)
        assert len(g["fs"]) == 2

    def test_dirs(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[ds; @glob.dirs["{tmp_path}"]]'
        g = run(src)
        assert len(g["ds"]) == 1

    def test_dirs_r(self, tmp_path):
        self._setup(tmp_path)
        sub2 = tmp_path / "sub" / "deep"
        sub2.mkdir()
        src = f'@var[ds; @glob.dirs_r["{tmp_path}"]]'
        g = run(src)
        assert len(g["ds"]) == 2

    def test_by_ext(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[fs; @glob.by_ext["{tmp_path}"; "txt"]]'
        g = run(src)
        assert len(g["fs"]) == 2

    def test_by_ext_dot(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[fs; @glob.by_ext["{tmp_path}"; ".py"]]'
        g = run(src)
        assert len(g["fs"]) == 1

    def test_by_ext_r(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[fs; @glob.by_ext_r["{tmp_path}"; "txt"]]'
        g = run(src)
        assert len(g["fs"]) == 3

    def test_count(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[n; @glob.count["{tmp_path}/*.txt"]]'
        g = run(src)
        assert g["n"] == 2

    def test_any_true(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[ok; @glob.any["{tmp_path}/*.txt"]]'
        g = run(src)
        assert g["ok"] is True

    def test_any_false(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[ok; @glob.any["{tmp_path}/*.xyz"]]'
        g = run(src)
        assert g["ok"] is False

    def test_first(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[f; @glob.first["{tmp_path}/*.txt"]]'
        g = run(src)
        assert g["f"] is not None
        assert g["f"].endswith(".txt")

    def test_first_none(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[f; @glob.first["{tmp_path}/*.xyz"]]'
        g = run(src)
        assert g["f"] is None

    def test_newest(self, tmp_path):
        self._setup(tmp_path)
        import time; time.sleep(0.01)
        newest = tmp_path / "newest.txt"
        newest.write_text("newest")
        src = f'@var[f; @glob.newest["{tmp_path}/*.txt"]]'
        g = run(src)
        assert g["f"].endswith("newest.txt")

    def test_sort_by_name(self, tmp_path):
        self._setup(tmp_path)
        src = f'@var[fs; @glob.sort_by_name["{tmp_path}/*.txt"]]'
        g = run(src)
        names = [os.path.basename(p) for p in g["fs"]]
        assert names == sorted(names)

    def test_sort_by_size(self, tmp_path):
        (tmp_path / "small.bin").write_bytes(b"x")
        (tmp_path / "large.bin").write_bytes(b"x" * 1000)
        src = f'@var[fs; @glob.sort_by_size["{tmp_path}/*.bin"]]'
        g = run(src)
        sizes = [os.path.getsize(p) for p in g["fs"]]
        assert sizes == sorted(sizes)

    def test_largest(self, tmp_path):
        (tmp_path / "small.bin").write_bytes(b"x")
        (tmp_path / "large.bin").write_bytes(b"x" * 1000)
        src = f'@var[f; @glob.largest["{tmp_path}/*.bin"]]'
        g = run(src)
        assert g["f"].endswith("large.bin")

    def test_escape(self):
        src = '@var[s; @glob.escape["file[1].txt"]]'
        g = run(src)
        assert "[" not in g["s"].replace("[[]", "")


# ─────────────────────────────────────────────────────────────
# @tempfile
# ─────────────────────────────────────────────────────────────

class TestTempfile:
    def test_file_no_args(self):
        src = "@var[p; @tempfile.file[]]"
        g = run(src)
        assert isinstance(g["p"], str)
        assert os.path.exists(g["p"])
        os.unlink(g["p"])

    def test_file_suffix(self):
        src = '@var[p; @tempfile.file[".txt"]]'
        g = run(src)
        assert g["p"].endswith(".txt")
        os.unlink(g["p"])

    def test_file_suffix_prefix(self):
        src = '@var[p; @tempfile.file[".tmp"; "cruhon_"]]'
        g = run(src)
        assert os.path.basename(g["p"]).startswith("cruhon_")
        assert g["p"].endswith(".tmp")
        os.unlink(g["p"])

    def test_named(self):
        src = '@var[p; @tempfile.named[".json"]]'
        g = run(src)
        assert g["p"].endswith(".json")
        os.unlink(g["p"])

    def test_in_dir(self, tmp_path):
        src = f'@var[p; @tempfile.in_dir["{tmp_path}"]]'
        g = run(src)
        assert str(tmp_path) in g["p"]
        os.unlink(g["p"])

    def test_dir_no_args(self):
        src = "@var[p; @tempfile.dir[]]"
        g = run(src)
        assert os.path.isdir(g["p"])
        os.rmdir(g["p"])

    def test_dir_prefix(self):
        src = '@var[p; @tempfile.dir["myprefix_"]]'
        g = run(src)
        assert os.path.basename(g["p"]).startswith("myprefix_")
        os.rmdir(g["p"])

    def test_in_dir_dir(self, tmp_path):
        src = f'@var[p; @tempfile.in_dir_dir["{tmp_path}"]]'
        g = run(src)
        assert str(tmp_path) in g["p"]
        os.rmdir(g["p"])

    def test_gettempdir(self):
        src = "@var[d; @tempfile.gettempdir[]]"
        g = run(src)
        assert os.path.isdir(g["d"])

    def test_mkstemp(self):
        src = "@var[result; @tempfile.mkstemp[]]"
        g = run(src)
        fd, path = g["result"]
        os.close(fd)
        assert os.path.exists(path)
        os.unlink(path)


# ─────────────────────────────────────────────────────────────
# @fnmatch
# ─────────────────────────────────────────────────────────────

class TestFnmatch:
    def test_match_true(self):
        g = run('@var[ok; @fnmatch.match["hello.txt"; "*.txt"]]')
        assert g["ok"] is True

    def test_match_false(self):
        g = run('@var[ok; @fnmatch.match["hello.py"; "*.txt"]]')
        assert g["ok"] is False

    def test_imatch_case(self):
        g = run('@var[ok; @fnmatch.imatch["Hello.TXT"; "*.txt"]]')
        assert g["ok"] is True

    def test_filter(self):
        g = run('@var[r; @fnmatch.filter[["a.txt", "b.py", "c.txt"]; "*.txt"]]')
        assert sorted(g["r"]) == ["a.txt", "c.txt"]

    def test_ifilter(self):
        g = run('@var[r; @fnmatch.ifilter[["A.TXT", "b.py", "C.Txt"]; "*.txt"]]')
        assert len(g["r"]) == 2

    def test_reject(self):
        g = run('@var[r; @fnmatch.reject[["a.txt", "b.py", "c.txt"]; "*.txt"]]')
        assert g["r"] == ["b.py"]

    def test_translate(self):
        g = run('@var[r; @fnmatch.translate["*.txt"]]')
        assert isinstance(g["r"], str)
        import re
        assert re.match(g["r"], "hello.txt")

    def test_any_match(self):
        g = run('@var[ok; @fnmatch.any_match["file.py"; ["*.txt", "*.py"]]]')
        assert g["ok"] is True

    def test_all_match(self):
        g = run('@var[ok; @fnmatch.all_match[["a.txt", "b.txt"]; "*.txt"]]')
        assert g["ok"] is True

    def test_all_match_false(self):
        g = run('@var[ok; @fnmatch.all_match[["a.txt", "b.py"]; "*.txt"]]')
        assert g["ok"] is False


# ─────────────────────────────────────────────────────────────
# @fileinput
# ─────────────────────────────────────────────────────────────

class TestFileinput:
    def _file(self, tmp_path, content="line1\nline2\nline3\n"):
        p = tmp_path / "test.txt"
        p.write_text(content, encoding="utf-8")
        return str(p)

    def test_lines(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[ls; @fileinput.lines["{p}"]]')
        assert g["ls"] == ["line1", "line2", "line3"]

    def test_lines_raw(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[ls; @fileinput.lines_raw["{p}"]]')
        assert all(l.endswith("\n") for l in g["ls"])

    def test_lines_multi(self, tmp_path):
        p1 = tmp_path / "f1.txt"
        p2 = tmp_path / "f2.txt"
        p1.write_text("a\nb\n")
        p2.write_text("c\nd\n")
        src = f'@var[ls; @fileinput.lines_multi[["{p1}", "{p2}"]]]'
        g = run(src)
        assert g["ls"] == ["a", "b", "c", "d"]

    def test_numbered(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[ns; @fileinput.numbered["{p}"]]')
        assert g["ns"][0] == (1, "line1")
        assert g["ns"][2] == (3, "line3")

    def test_head(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[ls; @fileinput.head["{p}"; 2]]')
        assert g["ls"] == ["line1", "line2"]

    def test_tail(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[ls; @fileinput.tail["{p}"; 2]]')
        assert g["ls"] == ["line2", "line3"]

    def test_slice(self, tmp_path):
        p = self._file(tmp_path, "a\nb\nc\nd\ne\n")
        g = run(f'@var[ls; @fileinput.slice["{p}"; 1; 3]]')
        assert g["ls"] == ["b", "c"]

    def test_grep(self, tmp_path):
        p = self._file(tmp_path, "apple\nbanana\napricot\n")
        g = run(f'@var[ls; @fileinput.grep["{p}"; "^ap"]]')
        assert sorted(g["ls"]) == ["apple", "apricot"]

    def test_grep_n(self, tmp_path):
        p = self._file(tmp_path, "apple\nbanana\napricot\n")
        g = run(f'@var[ls; @fileinput.grep_n["{p}"; "banana"]]')
        assert g["ls"] == [(2, "banana")]

    def test_contains_true(self, tmp_path):
        p = self._file(tmp_path, "hello world\n")
        g = run(f'@var[ok; @fileinput.contains["{p}"; "world"]]')
        assert g["ok"] is True

    def test_contains_false(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[ok; @fileinput.contains["{p}"; "xyz"]]')
        assert g["ok"] is False

    def test_count_lines(self, tmp_path):
        p = self._file(tmp_path)
        g = run(f'@var[n; @fileinput.count_lines["{p}"]]')
        assert g["n"] == 3

    def test_count_words(self, tmp_path):
        p = self._file(tmp_path, "one two three\nfour five\n")
        g = run(f'@var[n; @fileinput.count_words["{p}"]]')
        assert g["n"] == 5

    def test_count_chars(self, tmp_path):
        p = tmp_path / "t.txt"
        p.write_text("abc", encoding="utf-8")
        g = run(f'@var[n; @fileinput.count_chars["{p}"]]')
        assert g["n"] == 3

    def test_replace(self, tmp_path):
        p = self._file(tmp_path, "hello world\n")
        g = run(f'@var[s; @fileinput.replace["{p}"; "world"; "Cruhon"]]')
        assert g["s"] == "hello Cruhon\n"

    def test_replace_save(self, tmp_path):
        p = self._file(tmp_path, "foo bar foo\n")
        run(f'@fileinput.replace_save["{p}"; "foo"; "baz"]')
        assert Path(str(p)).read_text(encoding="utf-8") == "baz bar baz\n"

    def test_strip_empty(self, tmp_path):
        p = self._file(tmp_path, "a\n\nb\n\nc\n")
        g = run(f'@var[ls; @fileinput.strip_empty["{p}"]]')
        assert g["ls"] == ["a", "b", "c"]

    def test_unique_lines(self, tmp_path):
        p = self._file(tmp_path, "a\nb\na\nc\nb\n")
        g = run(f'@var[ls; @fileinput.unique_lines["{p}"]]')
        assert g["ls"] == ["a", "b", "c"]


# ─────────────────────────────────────────────────────────────
# @stat
# ─────────────────────────────────────────────────────────────

class TestStat:
    def test_of(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_text("x")
        g = run(f'@var[s; @stat.of["{p}"]]')
        import os as _os
        assert isinstance(g["s"], _os.stat_result)

    def test_mode(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_text("x")
        g = run(f'@var[m; @stat.mode["{p}"]]')
        assert isinstance(g["m"], int)

    def test_filemode(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_text("x")
        mode = p.stat().st_mode
        g = run(f'@var[s; @stat.filemode[{mode}]]')
        assert len(g["s"]) == 10
        assert g["s"][0] in ("-", "d", "l")

    def test_octal(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_text("x")
        p.chmod(0o644)
        mode = p.stat().st_mode
        g = run(f'@var[s; @stat.octal[{mode}]]')
        assert g["s"] == "644"

    def test_is_file(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_text("x")
        mode = p.stat().st_mode
        g = run(f'@var[ok; @stat.is_file[{mode}]]')
        assert g["ok"] is True

    def test_is_dir(self, tmp_path):
        mode = tmp_path.stat().st_mode
        g = run(f'@var[ok; @stat.is_dir[{mode}]]')
        assert g["ok"] is True

    def test_is_file_false_for_dir(self, tmp_path):
        mode = tmp_path.stat().st_mode
        g = run(f'@var[ok; @stat.is_file[{mode}]]')
        assert g["ok"] is False

    def test_perms(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_text("x")
        g = run(f'@var[s; @stat.perms["{p}"]]')
        assert len(g["s"]) == 9

    def test_readable(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_text("x")
        g = run(f'@var[ok; @stat.readable["{p}"]]')
        assert g["ok"] is True

    def test_writable(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_text("x")
        g = run(f'@var[ok; @stat.writable["{p}"]]')
        assert g["ok"] is True

    def test_executable(self, tmp_path):
        p = tmp_path / "script.sh"
        p.write_text("#!/bin/sh")
        p.chmod(0o755)
        g = run(f'@var[ok; @stat.executable["{p}"]]')
        assert g["ok"] is True

    def test_is_exec_mode(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_text("x")
        p.chmod(0o755)
        mode = p.stat().st_mode
        g = run(f'@var[ok; @stat.is_exec[{mode}]]')
        assert g["ok"] is True
