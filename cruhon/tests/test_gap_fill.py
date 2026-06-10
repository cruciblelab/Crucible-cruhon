"""
Tests for gap-fill additions — @file, @text, @date, @shell, @crypto, @archive expansions
"""
import os
import sys
import stat
import hashlib
import pytest

from cruhon.core.parser import parse
from cruhon.core.transpiler import transpile
from cruhon.core.runner import run_source, RunError


def _eval(expr_source: str):
    code = transpile(parse(f"@var[__r__; {expr_source}]"))
    ns: dict = {}
    exec(compile(code, "<test>", "exec"), ns)
    return ns["__r__"]


def _run(source: str):
    return run_source(source)


@pytest.fixture
def in_tmp(tmp_path):
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old)


# ════════════════════════════════════════════════════════════
#  @file — new commands
# ════════════════════════════════════════════════════════════

class TestFileNew:
    def test_touch_creates_file(self, in_tmp):
        _run('@file.touch["newfile.txt"]')
        assert (in_tmp / "newfile.txt").exists()

    def test_touch_updates_mtime(self, in_tmp):
        p = in_tmp / "t.txt"
        p.write_text("x")
        old_mtime = p.stat().st_mtime
        import time; time.sleep(0.05)
        _run('@file.touch["t.txt"]')
        assert p.stat().st_mtime >= old_mtime

    def test_chmod(self, in_tmp):
        (in_tmp / "ch.txt").write_text("x")
        _run('@file.chmod["ch.txt"; 420]')  # 420 == 0o644
        mode = stat.S_IMODE(os.stat(in_tmp / "ch.txt").st_mode)
        assert mode == 0o644

    def test_symlink(self, in_tmp):
        (in_tmp / "orig.txt").write_text("original")
        _run('@file.symlink["orig.txt"; "link.txt"]')
        assert _eval('@file.is_link["link.txt"]') is True
        assert (in_tmp / "link.txt").read_text() == "original"

    def test_is_link_false(self, in_tmp):
        (in_tmp / "plain.txt").write_text("x")
        assert _eval('@file.is_link["plain.txt"]') is False

    def test_stat(self, in_tmp):
        (in_tmp / "s.txt").write_text("hello")
        result = _eval('@file.stat["s.txt"]')
        assert result.st_size == 5

    def test_realpath(self, in_tmp):
        p = _eval(f'@file.realpath["{in_tmp}"]')
        assert os.path.isabs(p)

    def test_samefile(self, in_tmp):
        (in_tmp / "a.txt").write_text("x")
        assert _eval('@file.samefile["a.txt"; "a.txt"]') is True

    def test_expanduser(self):
        result = _eval('@file.expanduser["~"]')
        assert result == os.path.expanduser("~")

    def test_read_with_encoding(self, in_tmp):
        (in_tmp / "latin.txt").write_bytes("café".encode("latin-1"))
        result = _eval('@file.read["latin.txt"; "latin-1"]')
        assert result == "café"

    def test_write_with_encoding(self, in_tmp):
        _run('@file.write["latin2.txt"; "naïve"; "latin-1"]')
        raw = (in_tmp / "latin2.txt").read_bytes()
        assert raw == "naïve".encode("latin-1")

    def test_hardlink(self, in_tmp):
        (in_tmp / "hl_orig.txt").write_text("linked")
        _run('@file.hardlink["hl_orig.txt"; "hl_link.txt"]')
        assert (in_tmp / "hl_link.txt").read_text() == "linked"


# ════════════════════════════════════════════════════════════
#  @text — new commands
# ════════════════════════════════════════════════════════════

class TestTextNew:
    def test_casefold(self):
        assert _eval('@text.casefold["STRASSE"]') == "strasse"

    def test_expandtabs_default(self):
        result = _eval('@text.expandtabs["a\\tb"]')
        assert "\t" not in result
        assert "a" in result and "b" in result

    def test_expandtabs_custom(self):
        result = _eval('@text.expandtabs["a\\tb"; 4]')
        assert result == "a   b"

    def test_is_numeric(self):
        assert _eval('@text.is_numeric["123"]') is True
        assert _eval('@text.is_numeric["abc"]') is False

    def test_is_decimal(self):
        assert _eval('@text.is_decimal["123"]') is True
        assert _eval('@text.is_decimal["½"]') is False

    def test_is_identifier(self):
        assert _eval('@text.is_identifier["my_var"]') is True
        assert _eval('@text.is_identifier["123abc"]') is False

    def test_is_printable(self):
        assert _eval('@text.is_printable["hello"]') is True

    def test_is_ascii(self):
        assert _eval('@text.is_ascii["hello"]') is True
        assert _eval('@text.is_ascii["café"]') is False

    def test_rindex(self):
        assert _eval('@text.rindex["hello world hello"; "hello"]') == 12

    def test_rindex_missing(self):
        assert _eval('@text.rindex["hello"; "xyz"]') == -1

    def test_partition(self):
        result = _eval('@text.partition["hello world"; " "]')
        assert result == ("hello", " ", "world")

    def test_rpartition(self):
        result = _eval('@text.rpartition["a/b/c"; "/"]')
        assert result == ("a/b", "/", "c")

    def test_rsplit(self):
        result = _eval('@text.rsplit["a b c"; " "; 1]')
        assert result == ["a b", "c"]

    def test_translate_maketrans(self):
        code = transpile(parse(
            '@var[__t__; @text.maketrans["aeiou"; "AEIOU"]]\n'
            '@var[__r__; @text.translate["hello"; __t__]]'
        ))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] == "hEllO"

    def test_encode(self):
        result = _eval('@text.encode["hello"]')
        assert result == b"hello"

    def test_encode_custom(self):
        result = _eval('@text.encode["café"; "utf-8"]')
        assert result == "café".encode("utf-8")

    def test_decode(self):
        code = transpile(parse(
            '@var[__b__; @text.encode["hello"]]\n'
            '@var[__r__; @text.decode[__b__]]'
        ))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] == "hello"

    def test_ljust(self):
        assert _eval('@text.ljust["hi"; 5]') == "hi   "

    def test_rjust(self):
        assert _eval('@text.rjust["hi"; 5]') == "   hi"


# ════════════════════════════════════════════════════════════
#  @date — new commands
# ════════════════════════════════════════════════════════════

class TestDateNew:
    def test_timedelta(self):
        import datetime
        code = transpile(parse('@var[__r__; @date.timedelta[days=3; hours=2]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        td = ns["__r__"]
        assert td == datetime.timedelta(days=3, hours=2)

    def test_total_seconds(self):
        import datetime
        code = transpile(parse('@var[__r__; @date.total_seconds[@date.timedelta[hours=1]]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] == 3600.0

    def test_replace(self):
        import datetime
        code = transpile(parse('@var[__r__; @date.replace[@date.now[]; year=2000]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"].year == 2000

    def test_combine(self):
        import datetime
        code = transpile(parse(
            '@var[__d__; @date.today[]]\n'
            '@var[__t__; @date.make_time[10; 30; 0]]\n'
            '@var[__r__; @date.combine[__d__; __t__]]'
        ))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"].hour == 10
        assert ns["__r__"].minute == 30

    def test_microsecond(self):
        code = transpile(parse('@var[__r__; @date.microsecond[@date.now[]]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert isinstance(ns["__r__"], int)

    def test_isocalendar(self):
        code = transpile(parse('@var[__r__; @date.isocalendar[@date.today[]]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        cal = ns["__r__"]
        assert hasattr(cal, "week")
        assert 1 <= cal.week <= 53

    def test_isoweek(self):
        result = _eval('@date.isoweek[@date.today[]]')
        assert 1 <= result <= 53

    def test_isoyear(self):
        result = _eval('@date.isoyear[@date.today[]]')
        assert result >= 2020

    def test_utc_constant(self):
        import datetime
        code = transpile(parse('@var[__r__; @date.utc[]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] is datetime.timezone.utc

    def test_timezone(self):
        code = transpile(parse('@var[__r__; @date.timezone["UTC"]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert str(ns["__r__"]) == "UTC"

    def test_to_timezone(self):
        code = transpile(parse('@var[__r__; @date.to_timezone[@date.utcnow[]; "UTC"]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"].tzinfo is not None

    def test_make_time(self):
        import datetime
        code = transpile(parse('@var[__r__; @date.make_time[9; 30; 0]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] == datetime.time(9, 30, 0)


# ════════════════════════════════════════════════════════════
#  @shell — new commands
# ════════════════════════════════════════════════════════════

class TestShellNew:
    def test_bg_stdin(self):
        import subprocess
        proc = _eval('@shell.bg_stdin["cat"]')
        assert isinstance(proc, subprocess.Popen)
        proc.stdin.close()
        proc.wait()

    def test_kill(self):
        import subprocess
        p = subprocess.Popen("sleep 60", shell=True)
        code = transpile(parse('@shell.kill[__p__]'))
        ns = {"__p__": p}
        exec(compile(code, "<t>", "exec"), ns)
        p.wait()
        assert p.returncode is not None

    def test_terminate_and_wait(self):
        import subprocess
        p = subprocess.Popen("sleep 60", shell=True)
        code = transpile(parse('@shell.terminate[__p__]\n@shell.wait[__p__]'))
        ns = {"__p__": p}
        exec(compile(code, "<t>", "exec"), ns)
        assert p.returncode is not None

    def test_poll(self):
        import subprocess
        p = subprocess.Popen("true", shell=True)
        p.wait()
        code = transpile(parse('@var[__r__; @shell.poll[__p__]]'))
        ns = {"__p__": p}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] == 0

    def test_returncode(self):
        import subprocess
        p = subprocess.Popen("true", shell=True)
        p.wait()
        code = transpile(parse('@var[__r__; @shell.returncode[__p__]]'))
        ns = {"__p__": p}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] == 0

    def test_communicate(self):
        import subprocess
        p = subprocess.Popen("cat", shell=True, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, text=True)
        code = transpile(parse('@var[__r__; @shell.communicate[__p__; "hello"]]'))
        ns = {"__p__": p}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"][0] == "hello"

    def test_env_all(self):
        result = _eval('@shell.env_all[]')
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_cpu_count(self):
        n = _eval('@shell.cpu_count[]')
        assert isinstance(n, int)
        assert n >= 1

    def test_hostname(self):
        import socket
        h = _eval('@shell.hostname[]')
        assert h == socket.gethostname()

    def test_username(self):
        import getpass
        u = _eval('@shell.username[]')
        assert u == getpass.getuser()

    def test_home(self):
        h = _eval('@shell.home[]')
        assert os.path.isdir(h)


# ════════════════════════════════════════════════════════════
#  @crypto — new commands
# ════════════════════════════════════════════════════════════

class TestCryptoNew:
    def test_sha3_256(self):
        expected = hashlib.sha3_256(b"hello").hexdigest()
        assert _eval('@crypto.sha3_256["hello"]') == expected

    def test_sha3_512(self):
        expected = hashlib.sha3_512(b"hello").hexdigest()
        assert _eval('@crypto.sha3_512["hello"]') == expected

    def test_blake2b(self):
        expected = hashlib.blake2b(b"hello").hexdigest()
        assert _eval('@crypto.blake2b["hello"]') == expected

    def test_blake2s(self):
        expected = hashlib.blake2s(b"hello").hexdigest()
        assert _eval('@crypto.blake2s["hello"]') == expected

    def test_hash_file(self, in_tmp):
        (in_tmp / "hf.txt").write_bytes(b"file content")
        expected = hashlib.md5(b"file content").hexdigest()
        result = _eval('@crypto.hash_file["md5"; "hf.txt"]')
        assert result == expected

    def test_pbkdf2_default(self):
        result = _eval('@crypto.pbkdf2["password"; "salt"]')
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 → 32 bytes → 64 hex chars

    def test_pbkdf2_custom_iters(self):
        expected = hashlib.pbkdf2_hmac("sha256", b"pw", b"s", 1000).hex()
        result = _eval('@crypto.pbkdf2["pw"; "s"; 1000]')
        assert result == expected

    def test_scrypt(self):
        # small n=256 so the test runs quickly; default n=16384 is for production
        result = _eval('@crypto.scrypt["password"; "saltsalt"; 256; 8; 1]')
        assert isinstance(result, str)
        assert len(result) > 0


# ════════════════════════════════════════════════════════════
#  @archive — new compression formats
# ════════════════════════════════════════════════════════════

class TestArchiveNew:
    def test_bzip2_bunzip2_roundtrip(self, in_tmp):
        (in_tmp / "orig.txt").write_text("bzip2 content here")
        _run('@archive.bzip2["orig.txt"; "orig.txt.bz2"]')
        assert (in_tmp / "orig.txt.bz2").exists()
        _run('@archive.bunzip2["orig.txt.bz2"; "restored.txt"]')
        assert (in_tmp / "restored.txt").read_text() == "bzip2 content here"

    def test_lzma_unlzma_roundtrip(self, in_tmp):
        (in_tmp / "lz.txt").write_text("lzma content here")
        _run('@archive.lzma["lz.txt"; "lz.txt.xz"]')
        assert (in_tmp / "lz.txt.xz").exists()
        _run('@archive.unlzma["lz.txt.xz"; "lz_out.txt"]')
        assert (in_tmp / "lz_out.txt").read_text() == "lzma content here"


# ════════════════════════════════════════════════════════════
#  @http — new commands
# ════════════════════════════════════════════════════════════

class TestHttpNew:
    def test_elapsed_attribute(self):
        import requests
        r = requests.get("https://httpbin.org/get", timeout=10)
        code = transpile(parse('@var[__r__; @http.elapsed[__res__]]'))
        ns = {"__res__": r}
        exec(compile(code, "<t>", "exec"), ns)
        assert isinstance(ns["__r__"], float)
        assert ns["__r__"] >= 0

    def test_encoding_attribute(self):
        import requests
        r = requests.get("https://httpbin.org/get", timeout=10)
        code = transpile(parse('@var[__r__; @http.encoding[__res__]]'))
        ns = {"__res__": r}
        exec(compile(code, "<t>", "exec"), ns)
        assert isinstance(ns["__r__"], (str, type(None)))
