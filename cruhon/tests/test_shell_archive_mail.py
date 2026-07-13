"""
Tests for Group 4: @shell, @archive, @mail
"""
import os
import sys
import zipfile
import tarfile
import gzip
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
#  @shell — run / output
# ════════════════════════════════════════════════════════════

class TestShellRun:
    def test_run_returns_completed_process(self):
        result = _eval('@shell.run["echo hello"]')
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_output_strips_whitespace(self):
        out = _eval('@shell.output["echo   trimmed   "]')
        assert out == "trimmed"

    def test_lines(self):
        lines = _eval('@shell.lines["printf \'a\\nb\\nc\'"]')
        assert lines == ["a", "b", "c"]

    def test_code_zero(self):
        assert _eval('@shell.code["true"]') == 0

    def test_code_nonzero(self):
        assert _eval('@shell.code["false"]') != 0

    def test_ok_true(self):
        assert _eval('@shell.ok["true"]') is True

    def test_ok_false(self):
        assert _eval('@shell.ok["false"]') is False

    def test_bg_returns_popen(self):
        import subprocess
        proc = _eval('@shell.bg["sleep 0.01"]')
        assert isinstance(proc, subprocess.Popen)
        proc.wait()

    def test_pipe(self):
        result = _eval('@shell.pipe["echo hello world"; "tr a-z A-Z"]')
        assert result.strip() == "HELLO WORLD"


# ════════════════════════════════════════════════════════════
#  @shell — lookup
# ════════════════════════════════════════════════════════════

class TestShellLookup:
    def test_which_python(self):
        path = _eval('@shell.which["python3"]') or _eval('@shell.which["python"]')
        assert path is not None
        assert "python" in path.lower()

    def test_which_missing(self):
        result = _eval('@shell.which["__definitely_missing_cmd_xyz__"]')
        assert result is None

    def test_exists_true(self):
        assert _eval('@shell.exists["python3"]') is True or _eval('@shell.exists["python"]') is True

    def test_exists_false(self):
        assert _eval('@shell.exists["__definitely_missing_cmd_xyz__"]') is False


# ════════════════════════════════════════════════════════════
#  @shell — environment / process
# ════════════════════════════════════════════════════════════

class TestShellEnv:
    def test_env_get(self):
        os.environ["_SH_TEST_KEY"] = "myval"
        assert _eval('@shell.env["_SH_TEST_KEY"]') == "myval"
        del os.environ["_SH_TEST_KEY"]

    def test_env_default(self):
        result = _eval('@shell.env["_SH_MISSING_XYZ"; "fallback"]')
        assert result == "fallback"

    def test_env_set(self):
        _run('@shell.env_set["_SH_SET_TEST"; "99"]')
        assert os.environ.get("_SH_SET_TEST") == "99"
        del os.environ["_SH_SET_TEST"]

    def test_env_del(self):
        os.environ["_SH_DEL_TEST"] = "x"
        _run('@shell.env_del["_SH_DEL_TEST"]')
        assert "_SH_DEL_TEST" not in os.environ

    def test_cwd(self):
        cwd = _eval('@shell.cwd[]')
        assert os.path.isdir(cwd)

    def test_cd(self, in_tmp, tmp_path):
        _run(f'@shell.cd["{tmp_path}"]')
        assert os.getcwd() == str(tmp_path)

    def test_platform(self):
        plat = _eval('@shell.platform[]')
        assert isinstance(plat, str)
        assert len(plat) > 0

    def test_python_version(self):
        ver = _eval('@shell.python_version[]')
        assert isinstance(ver, str)
        assert "." in ver

    def test_pid(self):
        pid = _eval('@shell.pid[]')
        assert isinstance(pid, int)
        assert pid == os.getpid()

    def test_args(self):
        args = _eval('@shell.args[]')
        assert isinstance(args, list)


# ════════════════════════════════════════════════════════════
#  @archive — zip
# ════════════════════════════════════════════════════════════

class TestArchiveZip:
    def test_zip_single_file(self, in_tmp):
        (in_tmp / "hello.txt").write_text("hello")
        _run('@archive.zip["hello.txt"; "hello.zip"]')
        assert (in_tmp / "hello.zip").exists()
        with zipfile.ZipFile(in_tmp / "hello.zip") as zf:
            assert "hello.txt" in zf.namelist()

    def test_zip_adds_extension(self, in_tmp):
        (in_tmp / "f.txt").write_text("x")
        _run('@archive.zip["f.txt"; "f"]')
        assert (in_tmp / "f.zip").exists()

    def test_unzip(self, in_tmp):
        (in_tmp / "a.txt").write_text("content")
        _run('@archive.zip["a.txt"; "a.zip"]')
        out_dir = in_tmp / "extracted"
        out_dir.mkdir()
        _run(f'@archive.unzip["a.zip"; "{out_dir}"]')
        assert (out_dir / "a.txt").exists()
        assert (out_dir / "a.txt").read_text(encoding="utf-8") == "content"

    def test_zip_list(self, in_tmp):
        (in_tmp / "b.txt").write_text("b")
        _run('@archive.zip["b.txt"; "b.zip"]')
        names = _eval('@archive.zip_list["b.zip"]')
        assert "b.txt" in names

    def test_zip_read(self, in_tmp):
        (in_tmp / "r.txt").write_text("read me")
        _run('@archive.zip["r.txt"; "r.zip"]')
        content = _eval('@archive.zip_read["r.zip"; "r.txt"]')
        assert content == "read me"

    def test_zip_add(self, in_tmp):
        (in_tmp / "x.txt").write_text("x")
        (in_tmp / "y.txt").write_text("y")
        _run('@archive.zip["x.txt"; "xy.zip"]')
        _run('@archive.zip_add["xy.zip"; "y.txt"]')
        names = _eval('@archive.zip_list["xy.zip"]')
        assert "y.txt" in names

    def test_zip_extract_one(self, in_tmp):
        (in_tmp / "e.txt").write_text("extract me")
        _run('@archive.zip["e.txt"; "e.zip"]')
        out_dir = in_tmp / "single"
        out_dir.mkdir()
        _run(f'@archive.zip_extract_one["e.zip"; "e.txt"; "{out_dir}"]')
        assert (out_dir / "e.txt").read_text(encoding="utf-8") == "extract me"

    def test_is_zip_true(self, in_tmp):
        (in_tmp / "z.txt").write_text("z")
        _run('@archive.zip["z.txt"; "z.zip"]')
        assert _eval('@archive.is_zip["z.zip"]') is True

    def test_is_zip_false(self, in_tmp):
        (in_tmp / "plain.txt").write_text("not a zip")
        assert _eval('@archive.is_zip["plain.txt"]') is False

    def test_size_zip(self, in_tmp):
        (in_tmp / "s.txt").write_text("size test content")
        _run('@archive.zip["s.txt"; "s.zip"]')
        size = _eval('@archive.size["s.zip"]')
        assert size > 0


# ════════════════════════════════════════════════════════════
#  @archive — tar
# ════════════════════════════════════════════════════════════

class TestArchiveTar:
    def test_tar_single_file(self, in_tmp):
        (in_tmp / "t.txt").write_text("tar me")
        _run('@archive.tar["t.txt"; "t.tar.gz"]')
        assert (in_tmp / "t.tar.gz").exists()

    def test_tar_adds_extension(self, in_tmp):
        (in_tmp / "u.txt").write_text("u")
        _run('@archive.tar["u.txt"; "u"]')
        assert (in_tmp / "u.tar.gz").exists()

    def test_untar(self, in_tmp):
        (in_tmp / "v.txt").write_text("untar me")
        _run('@archive.tar["v.txt"; "v.tar.gz"]')
        out_dir = in_tmp / "tarout"
        out_dir.mkdir()
        _run(f'@archive.untar["v.tar.gz"; "{out_dir}"]')
        assert (out_dir / "v.txt").exists()

    def test_tar_list(self, in_tmp):
        (in_tmp / "l.txt").write_text("list")
        _run('@archive.tar["l.txt"; "l.tar.gz"]')
        names = _eval('@archive.tar_list["l.tar.gz"]')
        assert any("l.txt" in n for n in names)

    def test_is_tar_true(self, in_tmp):
        (in_tmp / "it.txt").write_text("tar")
        _run('@archive.tar["it.txt"; "it.tar.gz"]')
        assert _eval('@archive.is_tar["it.tar.gz"]') is True

    def test_size_tar(self, in_tmp):
        (in_tmp / "ts.txt").write_text("tar size content")
        _run('@archive.tar["ts.txt"; "ts.tar.gz"]')
        size = _eval('@archive.size["ts.tar.gz"]')
        assert size > 0


# ════════════════════════════════════════════════════════════
#  @archive — gzip
# ════════════════════════════════════════════════════════════

class TestArchiveGzip:
    def test_gzip_gunzip_roundtrip(self, in_tmp):
        (in_tmp / "orig.txt").write_text("gzip content here")
        _run('@archive.gzip["orig.txt"; "orig.txt.gz"]')
        assert (in_tmp / "orig.txt.gz").exists()
        _run('@archive.gunzip["orig.txt.gz"; "restored.txt"]')
        assert (in_tmp / "restored.txt").read_text(encoding="utf-8") == "gzip content here"


# ════════════════════════════════════════════════════════════
#  @archive — zip directory
# ════════════════════════════════════════════════════════════

class TestArchiveDirectory:
    def test_zip_directory(self, in_tmp):
        d = in_tmp / "mydir"
        d.mkdir()
        (d / "a.txt").write_text("a")
        (d / "b.txt").write_text("b")
        _run('@archive.zip["mydir"; "mydir.zip"]')
        names = _eval('@archive.zip_list["mydir.zip"]')
        assert any("a.txt" in n for n in names)
        assert any("b.txt" in n for n in names)


# ════════════════════════════════════════════════════════════
#  @mail — build / parse (no SMTP connection needed)
# ════════════════════════════════════════════════════════════

class TestMailBuild:
    def test_message_subject(self):
        code = transpile(parse('@var[__r__; @mail.message["Hello"; "Body text"]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        msg = ns["__r__"]
        assert msg["Subject"] == "Hello"

    def test_message_body(self):
        code = transpile(parse('@var[__r__; @mail.message["Subj"; "My body"]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        msg = ns["__r__"]
        payload = msg.get_payload(decode=True)
        assert payload is not None
        assert b"My body" in payload

    def test_html_message(self):
        code = transpile(parse('@var[__r__; @mail.html_message["Hi"; "<b>Bold</b>"]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        msg = ns["__r__"]
        assert msg["Subject"] == "Hi"
        assert msg.get_content_type() == "text/html"

    def test_parse_subject(self):
        import email as _email
        raw = "From: sender@example.com\nSubject: Test Subject\n\nBody"
        msg = _email.message_from_string(raw)
        code = transpile(parse('@var[__r__; @mail.subject[__msg__]]'))
        ns = {"__msg__": msg}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] == "Test Subject"

    def test_parse_sender(self):
        import email as _email
        raw = "From: alice@example.com\nSubject: Hi\n\nBody"
        msg = _email.message_from_string(raw)
        code = transpile(parse('@var[__r__; @mail.sender[__msg__]]'))
        ns = {"__msg__": msg}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] == "alice@example.com"

    def test_parse_body(self):
        import email as _email
        raw = "From: x@x.com\nSubject: S\n\nHello body"
        msg = _email.message_from_string(raw)
        code = transpile(parse('@var[__r__; @mail.body[__msg__]]'))
        ns = {"__msg__": msg}
        exec(compile(code, "<t>", "exec"), ns)
        assert "Hello body" in ns["__r__"]

    def test_parse_roundtrip(self):
        from email import message_from_string
        raw = "From: test@example.com\nSubject: Round Trip\n\nThe body text"
        msg = message_from_string(raw)
        assert msg["Subject"] == "Round Trip"
        assert msg["From"] == "test@example.com"

    def test_attach_adds_part(self, in_tmp):
        from email.mime.multipart import MIMEMultipart
        from cruhon.core.libs.mail_ import _attach
        (in_tmp / "attach.txt").write_text("attached content")
        msg = MIMEMultipart()
        msg["Subject"] = "S"
        _attach(msg, str(in_tmp / "attach.txt"))
        parts = msg.get_payload()
        assert len(parts) == 1
        assert parts[0].get_filename() == "attach.txt"
