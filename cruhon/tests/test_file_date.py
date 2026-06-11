"""
Tests for the expanded @file and new @date stdlib wrappers.
"""
import os
import json
import datetime
import pytest

from cruhon.core.runner import run_source, RunError
from cruhon.core.parser import parse
from cruhon.core.transpiler import transpile


def _run(source: str):
    return run_source(source)


def _eval(expr_source: str):
    """Transpile + exec a single @var assignment and return the value."""
    code = transpile(parse(f"@var[__r__; {expr_source}]"))
    ns: dict = {}
    exec(compile(code, "<test>", "exec"), ns)
    return ns["__r__"]


@pytest.fixture
def in_tmp(tmp_path):
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old)


# ════════════════════════════════════════════════════════════
#  @file — read / write
# ════════════════════════════════════════════════════════════

class TestFileReadWrite:
    def test_write_read(self, in_tmp):
        _run('@file.write["a.txt"; "merhaba"]')
        assert _eval('@file.read["a.txt"]') == "merhaba"

    def test_append(self, in_tmp):
        _run('@file.write["a.txt"; "bir"]')
        _run('@file.append["a.txt"; "iki"]')
        assert _eval('@file.read["a.txt"]') == "biriki"

    def test_lines(self, in_tmp):
        (in_tmp / "a.txt").write_text("x\ny\nz")
        assert _eval('@file.lines["a.txt"]') == ["x", "y", "z"]

    def test_bytes(self, in_tmp):
        (in_tmp / "a.bin").write_bytes(b"\x00\x01\x02")
        assert _eval('@file.bytes["a.bin"]') == b"\x00\x01\x02"

    def test_write_bytes(self, in_tmp):
        _run('@file.write_bytes["a.bin"; b"\\x00\\xff"]')
        assert (in_tmp / "a.bin").read_bytes() == b"\x00\xff"

    def test_write_creates_parent_dirs(self, in_tmp):
        _run('@file.write["deep/nested/a.txt"; "ok"]')
        assert (in_tmp / "deep" / "nested" / "a.txt").read_text() == "ok"

    def test_utf8_roundtrip(self, in_tmp):
        _run('@file.write["t.txt"; "hello 日本"]')
        assert _eval('@file.read["t.txt"]') == "hello 日本"


class TestFileJson:
    def test_write_read_json(self, in_tmp):
        _run('@file.write_json["d.json"; {"ad": "Ali", "yas": 25}]')
        assert _eval('@file.read_json["d.json"]') == {"ad": "Ali", "yas": 25}

    def test_write_json_is_pretty(self, in_tmp):
        _run('@file.write_json["d.json"; {"k": 1}]')
        text = (in_tmp / "d.json").read_text()
        assert "\n" in text  # indent=2 produces newlines


class TestFileExistenceType:
    def test_exists(self, in_tmp):
        assert _eval('@file.exists["x.txt"]') is False
        (in_tmp / "x.txt").write_text("y")
        assert _eval('@file.exists["x.txt"]') is True

    def test_is_file_is_dir(self, in_tmp):
        (in_tmp / "f.txt").write_text("y")
        (in_tmp / "d").mkdir()
        assert _eval('@file.is_file["f.txt"]') is True
        assert _eval('@file.is_dir["f.txt"]') is False
        assert _eval('@file.is_dir["d"]') is True

    def test_size(self, in_tmp):
        (in_tmp / "f.txt").write_text("12345")
        assert _eval('@file.size["f.txt"]') == 5


class TestFileCopyMoveDelete:
    def test_copy(self, in_tmp):
        (in_tmp / "a.txt").write_text("data")
        _run('@file.copy["a.txt"; "b.txt"]')
        assert (in_tmp / "b.txt").read_text() == "data"

    def test_copy_creates_parent(self, in_tmp):
        (in_tmp / "a.txt").write_text("data")
        _run('@file.copy["a.txt"; "out/b.txt"]')
        assert (in_tmp / "out" / "b.txt").read_text() == "data"

    def test_copytree(self, in_tmp):
        (in_tmp / "src").mkdir()
        (in_tmp / "src" / "f.txt").write_text("x")
        _run('@file.copytree["src"; "dst"]')
        assert (in_tmp / "dst" / "f.txt").read_text() == "x"

    def test_move(self, in_tmp):
        (in_tmp / "a.txt").write_text("data")
        _run('@file.move["a.txt"; "b.txt"]')
        assert not (in_tmp / "a.txt").exists()
        assert (in_tmp / "b.txt").read_text() == "data"

    def test_rename(self, in_tmp):
        (in_tmp / "a.txt").write_text("data")
        _run('@file.rename["a.txt"; "b.txt"]')
        assert (in_tmp / "b.txt").read_text() == "data"

    def test_delete(self, in_tmp):
        (in_tmp / "a.txt").write_text("data")
        _run('@file.delete["a.txt"]')
        assert not (in_tmp / "a.txt").exists()

    def test_rmdir(self, in_tmp):
        (in_tmp / "d").mkdir()
        (in_tmp / "d" / "f.txt").write_text("x")
        _run('@file.rmdir["d"]')
        assert not (in_tmp / "d").exists()


class TestFileDirsListing:
    def test_mkdir(self, in_tmp):
        _run('@file.mkdir["a/b/c"]')
        assert (in_tmp / "a" / "b" / "c").is_dir()

    def test_mkdir_idempotent(self, in_tmp):
        _run('@file.mkdir["d"]')
        _run('@file.mkdir["d"]')  # no error on existing
        assert (in_tmp / "d").is_dir()

    def test_list(self, in_tmp):
        (in_tmp / "a.txt").write_text("")
        (in_tmp / "b.txt").write_text("")
        assert _eval('@file.list["."]') == ["a.txt", "b.txt"]

    def test_glob(self, in_tmp):
        (in_tmp / "a.txt").write_text("")
        (in_tmp / "b.txt").write_text("")
        (in_tmp / "c.md").write_text("")
        assert _eval('@file.glob["*.txt"]') == ["a.txt", "b.txt"]

    def test_walk(self, in_tmp):
        (in_tmp / "sub").mkdir()
        (in_tmp / "sub" / "deep.txt").write_text("")
        (in_tmp / "top.txt").write_text("")
        result = _eval('@file.walk["."]')
        names = sorted(os.path.basename(p) for p in result)
        assert names == ["deep.txt", "top.txt"]


class TestFilePathHelpers:
    def test_join(self):
        assert _eval('@file.join["a"; "b"; "c"]') == os.path.join("a", "b", "c")

    def test_basename(self):
        assert _eval('@file.basename["/x/y/a.txt"]') == "a.txt"

    def test_dirname(self):
        assert _eval('@file.dirname["/x/y/a.txt"]') == "/x/y"

    def test_ext(self):
        assert _eval('@file.ext["a.tar.gz"]') == ".gz"

    def test_stem(self):
        assert _eval('@file.stem["/x/y/a.txt"]') == "a"

    def test_cwd(self, in_tmp):
        assert _eval('@file.cwd[]') == os.getcwd()

    def test_abspath(self, in_tmp):
        assert _eval('@file.abspath["a.txt"]') == str(in_tmp / "a.txt")


class TestFileTemp:
    def test_temp(self):
        p = _eval('@file.temp[]')
        assert os.path.exists(p)
        os.remove(p)

    def test_tempdir(self):
        p = _eval('@file.tempdir[]')
        assert os.path.isdir(p)
        os.rmdir(p)


class TestFileAnyPath:
    def test_read_absolute(self, tmp_path):
        f = tmp_path / "abs.txt"
        f.write_text("hello")
        assert _eval(f'@file.read["{f}"]') == "hello"

    def test_write_absolute(self, tmp_path):
        p = str(tmp_path / "out.txt")
        _run(f'@file.write["{p}"; "ok"]')
        assert (tmp_path / "out.txt").read_text() == "ok"


# ════════════════════════════════════════════════════════════
#  @date
# ════════════════════════════════════════════════════════════

class TestDateCurrent:
    def test_now(self):
        v = _eval('@date.now[]')
        assert isinstance(v, datetime.datetime)

    def test_today(self):
        v = _eval('@date.today[]')
        assert isinstance(v, datetime.date)

    def test_timestamp(self):
        v = _eval('@date.timestamp[]')
        assert isinstance(v, float)


class TestDateFormatParse:
    def test_format_now(self):
        v = _eval('@date.format["%Y"]')
        assert v == str(datetime.datetime.now().year)

    def test_format_dt(self):
        assert _eval('@date.format[@date.make[2024; 1; 15]; "%Y-%m-%d"]') == "2024-01-15"

    def test_parse(self):
        v = _eval('@date.parse["2024-03-10"; "%Y-%m-%d"]')
        assert v == datetime.datetime(2024, 3, 10)

    def test_iso_roundtrip(self):
        v = _eval('@date.from_iso["2024-03-10T12:30:00"]')
        assert v == datetime.datetime(2024, 3, 10, 12, 30, 0)

    def test_from_timestamp(self):
        v = _eval('@date.from_timestamp[0]')
        assert isinstance(v, datetime.datetime)


class TestDateArithmetic:
    def test_add_days(self):
        base = datetime.datetime(2024, 1, 1)
        v = _eval('@date.add[@date.make[2024; 1; 1; 0; 0]; days=10]')
        assert v == base + datetime.timedelta(days=10)

    def test_sub_days(self):
        base = datetime.datetime(2024, 1, 15)
        v = _eval('@date.sub[@date.make[2024; 1; 15; 0; 0]; days=5]')
        assert v == base - datetime.timedelta(days=5)

    def test_diff_days(self):
        v = _eval('@date.diff_days[@date.make[2024; 1; 11]; @date.make[2024; 1; 1]]')
        assert v == 10

    def test_diff_seconds(self):
        v = _eval('@date.diff_seconds[@date.make[2024; 1; 1; 1; 0]; @date.make[2024; 1; 1; 0; 0]]')
        assert v == 3600.0


class TestDateComponents:
    def test_components(self):
        assert _eval('@date.year[@date.make[2024; 3; 15; 10; 30]]') == 2024
        assert _eval('@date.month[@date.make[2024; 3; 15; 10; 30]]') == 3
        assert _eval('@date.day[@date.make[2024; 3; 15; 10; 30]]') == 15
        assert _eval('@date.hour[@date.make[2024; 3; 15; 10; 30]]') == 10
        assert _eval('@date.minute[@date.make[2024; 3; 15; 10; 30]]') == 30

    def test_weekday(self):
        # 2024-01-01 is a Monday → 0
        assert _eval('@date.weekday[@date.make[2024; 1; 1]]') == 0

    def test_weekday_name(self):
        assert _eval('@date.weekday_name[@date.make[2024; 1; 1]]') == "Monday"

    def test_month_name(self):
        assert _eval('@date.month_name[@date.make[2024; 1; 1]]') == "January"

    def test_is_weekend(self):
        # 2024-01-06 is Saturday
        assert _eval('@date.is_weekend[@date.make[2024; 1; 6]]') is True
        assert _eval('@date.is_weekend[@date.make[2024; 1; 1]]') is False


class TestDateBuild:
    def test_make_date(self):
        assert _eval('@date.make[2024; 1; 15]') == datetime.date(2024, 1, 15)

    def test_make_datetime(self):
        assert _eval('@date.make[2024; 1; 15; 10; 30]') == datetime.datetime(2024, 1, 15, 10, 30)

    def test_days_in_month(self):
        assert _eval('@date.days_in_month[2024; 2]') == 29  # leap year
        assert _eval('@date.days_in_month[2023; 2]') == 28


class TestDateCoercion:
    """@date.* should accept both datetime objects and ISO strings."""
    def test_format_iso_string(self):
        assert _eval('@date.format["2024-01-15"; "%Y/%m/%d"]') == "2024/01/15"

    def test_weekday_from_string(self):
        assert _eval('@date.weekday["2024-01-01"]') == 0
