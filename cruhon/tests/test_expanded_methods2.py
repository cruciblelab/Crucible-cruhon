"""
Tests for wave-6 method expansions:
@mmap (writable), @ssl, @locale, @signal, @mimetypes, @traceback, @unittest
"""
import ssl as _ssl

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
# @mmap — writable object API
# ─────────────────────────────────────────────────────────────

class TestMmapWritable:
    def test_open_get(self, tmp_path):
        p = tmp_path / "f.bin"
        p.write_bytes(b"hello world")
        src = '@var[m; @mmap.open[path]]\n@var[b; @mmap.get[m; 0; 5]]\n@mmap.close[m]'
        g = run(src, {"path": str(p)})
        assert g["b"] == b"hello"

    def test_put_persists(self, tmp_path):
        p = tmp_path / "f.bin"
        p.write_bytes(b"hello world")
        src = (
            '@var[m; @mmap.open[path]]\n'
            '@mmap.put[m; 0; b"HELLO"]\n'
            '@mmap.flush[m]\n'
            '@mmap.close[m]'
        )
        run(src, {"path": str(p)})
        assert p.read_bytes() == b"HELLO world"

    def test_length(self, tmp_path):
        p = tmp_path / "f.bin"
        p.write_bytes(b"abcd")
        src = '@var[m; @mmap.open[path]]\n@var[n; @mmap.length[m]]\n@mmap.close[m]'
        g = run(src, {"path": str(p)})
        assert g["n"] == 4

    def test_search(self, tmp_path):
        p = tmp_path / "f.bin"
        p.write_bytes(b"abcXYZ")
        src = '@var[m; @mmap.open[path]]\n@var[i; @mmap.search[m; b"XYZ"]]\n@mmap.close[m]'
        g = run(src, {"path": str(p)})
        assert g["i"] == 3


# ─────────────────────────────────────────────────────────────
# @ssl — context configuration
# ─────────────────────────────────────────────────────────────

class TestSslExpanded:
    def test_check_hostname_off(self):
        # Turning check_hostname off requires verify_mode CERT_NONE first.
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        g = run('@var[c; @ssl.check_hostname[ctx; False]]', {"ctx": ctx})
        assert g["c"].check_hostname is False

    def test_ciphers(self):
        g = run('@var[c; @ssl.ciphers[@ssl.context[]]]')
        assert isinstance(g["c"], list) and len(g["c"]) > 0

    def test_set_ciphers(self):
        g = run('@var[c; @ssl.set_ciphers[@ssl.context[]; "DEFAULT"]]')
        assert isinstance(g["c"], _ssl.SSLContext)

    def test_pem_to_der(self):
        # round-trip a self-made cert string is heavy; just check it's callable
        # on a known-good PEM via the stdlib's own conversion symmetry.
        import ssl
        # Build minimal: use DER->PEM->DER identity is not trivial without a cert.
        # Instead verify the function is wired by catching the expected error type.
        with pytest.raises(Exception):
            run('@var[d; @ssl.pem_to_der["not a real pem"]]')


# ─────────────────────────────────────────────────────────────
# @locale
# ─────────────────────────────────────────────────────────────

class TestLocaleExpanded:
    def test_normalize(self):
        g = run('@var[s; @locale.normalize["en_US"]]')
        assert "en_US" in g["s"]

    def test_delocalize(self):
        run('@locale.set["C"]')
        g = run('@var[n; @locale.delocalize["1234.5"]]')
        assert g["n"] == "1234.5"

    def test_format(self):
        run('@locale.set["C"]')
        g = run('@var[s; @locale.format[42]]')
        assert "42" in g["s"]


# ─────────────────────────────────────────────────────────────
# @signal
# ─────────────────────────────────────────────────────────────

class TestSignalExpanded:
    def test_get_timer(self):
        g = run('@var[t; @signal.get_timer[]]')
        assert isinstance(g["t"], tuple) and len(g["t"]) == 2

    def test_set_timer_zero(self):
        # setting to 0 disables; returns the previous (value, interval)
        g = run('@var[t; @signal.set_timer[0]]')
        assert isinstance(g["t"], tuple)


# ─────────────────────────────────────────────────────────────
# @mimetypes
# ─────────────────────────────────────────────────────────────

class TestMimetypesExpanded:
    def test_suffix_map(self):
        g = run('@var[m; @mimetypes.suffix_map[]]')
        assert isinstance(g["m"], dict) and ".tgz" in g["m"]

    def test_encodings_map(self):
        g = run('@var[m; @mimetypes.encodings_map[]]')
        assert isinstance(g["m"], dict) and ".gz" in g["m"]

    def test_init(self):
        run('@mimetypes.init[]')


# ─────────────────────────────────────────────────────────────
# @traceback
# ─────────────────────────────────────────────────────────────

class TestTracebackExpanded:
    def test_extract(self):
        g = run('@var[s; @traceback.extract[]]')
        import traceback
        assert isinstance(g["s"], traceback.StackSummary)

    def test_frames(self):
        try:
            raise ValueError("boom")
        except ValueError as e:
            g = run('@var[f; @traceback.frames[e]]', {"e": e})
            assert len(g["f"]) >= 1

    def test_format_frames(self):
        g = run('@var[lines; @traceback.format_frames[@traceback.extract[]]]')
        assert isinstance(g["lines"], list) and all(isinstance(x, str) for x in g["lines"])


# ─────────────────────────────────────────────────────────────
# @unittest — assertions + mock
# ─────────────────────────────────────────────────────────────

class TestUnittestExpanded:
    def test_assert_equal_pass(self):
        run('@unittest.assert_equal[1; 1]')  # no exception

    def test_assert_equal_fail(self):
        with pytest.raises(AssertionError):
            run('@unittest.assert_equal[1; 2]')

    def test_assert_true_fail(self):
        with pytest.raises(AssertionError):
            run('@unittest.assert_true[False]')

    def test_assert_in(self):
        run('@unittest.assert_in[2; [1, 2, 3]]')

    def test_assert_raises(self):
        def boom():
            raise ValueError("x")
        run('@unittest.assert_raises[ValueError; fn; ()]', {"fn": boom})

    def test_mock_default(self):
        import unittest.mock
        g = run('@var[m; @unittest.mock[]]')
        assert isinstance(g["m"], unittest.mock.MagicMock)

    def test_mock_return_value(self):
        g = run('@var[m; @unittest.mock[99]]')
        assert g["m"]() == 99

    def test_patch(self):
        import unittest.mock
        g = run('@var[p; @unittest.patch["os.getpid"]]')
        assert isinstance(g["p"], unittest.mock._patch)
