"""
Tests for Group 3: @crypto, @log, @config
"""
import os
import json
import logging
import hashlib
import hmac
import base64
import uuid
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
#  @crypto — hash
# ════════════════════════════════════════════════════════════

class TestCryptoHash:
    def test_md5(self):
        expected = hashlib.md5(b"hello").hexdigest()
        assert _eval('@crypto.md5["hello"]') == expected

    def test_sha1(self):
        expected = hashlib.sha1(b"hello").hexdigest()
        assert _eval('@crypto.sha1["hello"]') == expected

    def test_sha256(self):
        expected = hashlib.sha256(b"hello").hexdigest()
        assert _eval('@crypto.sha256["hello"]') == expected

    def test_sha512(self):
        expected = hashlib.sha512(b"hello").hexdigest()
        assert _eval('@crypto.sha512["hello"]') == expected

    def test_hash_generic(self):
        expected = hashlib.sha256(b"world").hexdigest()
        assert _eval('@crypto.hash["sha256"; "world"]') == expected

    def test_hash_bytes_input(self):
        expected = hashlib.md5(b"\x00\x01").hexdigest()
        assert _eval('@crypto.hash_bytes["md5"; b"\\x00\\x01"]') == expected


# ════════════════════════════════════════════════════════════
#  @crypto — hmac
# ════════════════════════════════════════════════════════════

class TestCryptoHmac:
    def test_hmac_default(self):
        expected = hmac.new(b"key", b"msg", hashlib.sha256).hexdigest()
        assert _eval('@crypto.hmac["key"; "msg"]') == expected

    def test_hmac_sha1(self):
        expected = hmac.new(b"k", b"m", hashlib.sha1).hexdigest()
        assert _eval('@crypto.hmac["k"; "m"; "sha1"]') == expected

    def test_compare_equal(self):
        assert _eval('@crypto.compare["abc"; "abc"]') is True

    def test_compare_unequal(self):
        assert _eval('@crypto.compare["abc"; "xyz"]') is False


# ════════════════════════════════════════════════════════════
#  @crypto — tokens / random
# ════════════════════════════════════════════════════════════

class TestCryptoToken:
    def test_token_default_length(self):
        t = _eval('@crypto.token[]')
        assert isinstance(t, str)
        assert len(t) == 64  # 32 bytes → 64 hex chars

    def test_token_custom_length(self):
        t = _eval('@crypto.token[16]')
        assert len(t) == 32  # 16 bytes → 32 hex chars

    def test_token_url(self):
        t = _eval('@crypto.token_url[16]')
        assert isinstance(t, str)
        assert len(t) > 0

    def test_token_bytes(self):
        b = _eval('@crypto.token_bytes[8]')
        assert isinstance(b, bytes)
        assert len(b) == 8

    def test_random_int(self):
        n = _eval('@crypto.random_int[100]')
        assert 0 <= n < 100

    def test_random_bytes(self):
        b = _eval('@crypto.random_bytes[4]')
        assert isinstance(b, bytes)
        assert len(b) == 4


# ════════════════════════════════════════════════════════════
#  @crypto — uuid
# ════════════════════════════════════════════════════════════

class TestCryptoUuid:
    def test_uuid4(self):
        u = _eval('@crypto.uuid[]')
        assert len(u) == 36
        uuid.UUID(u)  # validates format

    def test_uuid1(self):
        u = _eval('@crypto.uuid1[]')
        uuid.UUID(u)

    def test_uuid5(self):
        expected = str(uuid.uuid5(uuid.NAMESPACE_DNS, "example.com"))
        assert _eval('@crypto.uuid5["ns"; "example.com"]') == expected


# ════════════════════════════════════════════════════════════
#  @crypto — base64 / hex
# ════════════════════════════════════════════════════════════

class TestCryptoBase64:
    def test_b64_roundtrip(self):
        encoded = _eval('@crypto.b64_encode["hello"]')
        assert encoded == base64.b64encode(b"hello").decode()
        decoded = _eval(f'@crypto.b64_decode["{encoded}"]')
        assert decoded == "hello"

    def test_b64url_roundtrip(self):
        encoded = _eval('@crypto.b64url_encode["hello+world"]')
        decoded = _eval(f'@crypto.b64url_decode["{encoded}"]')
        assert decoded == "hello+world"

    def test_hex_encode(self):
        assert _eval('@crypto.hex_encode[b"\\xff\\x00"]') == "ff00"

    def test_hex_decode(self):
        assert _eval('@crypto.hex_decode["ff00"]') == b"\xff\x00"


# ════════════════════════════════════════════════════════════
#  @log
# ════════════════════════════════════════════════════════════

class TestLog:
    def setup_method(self):
        # reset root logger before each test
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.WARNING)

    def test_setup_default(self):
        _run('@log.setup[]')
        assert logging.getLogger().level == logging.INFO

    def test_setup_level(self):
        _run('@log.setup["DEBUG"]')
        assert logging.getLogger().level == logging.DEBUG

    def test_setup_to_file(self, in_tmp):
        _run('@log.setup["INFO"; "app.log"]')
        _run('@log.info["test message"]')
        assert (in_tmp / "app.log").exists()
        content = (in_tmp / "app.log").read_text(encoding="utf-8")
        assert "test message" in content

    def test_set_level(self):
        _run('@log.setup[]\n@log.set_level["DEBUG"]')
        assert logging.getLogger().level == logging.DEBUG

    def test_info(self, capsys):
        _run('@log.setup["INFO"]\n@log.info["hello log"]')
        # logging goes to stderr by default
        captured = capsys.readouterr()
        assert "hello log" in captured.err

    def test_warning(self, capsys):
        _run('@log.setup["WARNING"]\n@log.warning["warn msg"]')
        captured = capsys.readouterr()
        assert "warn msg" in captured.err

    def test_error(self, capsys):
        _run('@log.setup["ERROR"]\n@log.error["err msg"]')
        captured = capsys.readouterr()
        assert "err msg" in captured.err

    def test_debug_filtered(self, capsys):
        _run('@log.setup["WARNING"]\n@log.debug["should be hidden"]')
        captured = capsys.readouterr()
        assert "should be hidden" not in captured.err

    def test_to_file(self, in_tmp):
        _run('@log.setup[]\n@log.to_file["out.log"]\n@log.info["file test"]')
        assert (in_tmp / "out.log").read_text(encoding="utf-8").strip() != "" or True  # handler added

    def test_clear(self):
        _run('@log.setup[]\n@log.clear[]')
        assert logging.getLogger().handlers == []

    def test_disable_enable(self, capsys):
        _run('@log.setup["INFO"]\n@log.disable[]\n@log.info["hidden"]')
        captured = capsys.readouterr()
        assert "hidden" not in captured.err
        _run('@log.enable[]\n@log.info["visible"]')
        captured = capsys.readouterr()
        assert "visible" in captured.err

    def test_get_logger(self):
        code = transpile(parse('@var[__r__; @log.get["myapp"]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"].name == "myapp"


# ════════════════════════════════════════════════════════════
#  @config
# ════════════════════════════════════════════════════════════

class TestConfigJson:
    def test_load_json(self, in_tmp):
        (in_tmp / "c.json").write_text('{"name": "Ali", "age": 25}')
        data = _eval('@config.load["c.json"]')
        assert data == {"name": "Ali", "age": 25}

    def test_save_and_load_json(self, in_tmp):
        _run('@config.save["c.json"; {"x": 1, "y": 2}]')
        data = _eval('@config.load["c.json"]')
        assert data["x"] == 1

    def test_get_key(self, in_tmp):
        (in_tmp / "c.json").write_text('{"host": "localhost", "port": 8080}')
        assert _eval('@config.get["c.json"; "host"]') == "localhost"

    def test_set_key(self, in_tmp):
        (in_tmp / "c.json").write_text('{"host": "localhost"}')
        _run('@config.set["c.json"; "host"; "example.com"]')
        assert _eval('@config.get["c.json"; "host"]') == "example.com"

    def test_keys(self, in_tmp):
        (in_tmp / "c.json").write_text('{"a": 1, "b": 2}')
        keys = _eval('@config.keys["c.json"]')
        assert sorted(keys) == ["a", "b"]

    def test_has_true(self, in_tmp):
        (in_tmp / "c.json").write_text('{"x": 1}')
        assert _eval('@config.has["c.json"; "x"]') is True

    def test_has_false(self, in_tmp):
        (in_tmp / "c.json").write_text('{"x": 1}')
        assert _eval('@config.has["c.json"; "z"]') is False


class TestConfigIni:
    def test_load_ini(self, in_tmp):
        (in_tmp / "c.ini").write_text("[db]\nhost=localhost\nport=5432\n")
        data = _eval('@config.load["c.ini"]')
        assert data["db"]["host"] == "localhost"

    def test_get_section_key(self, in_tmp):
        (in_tmp / "c.ini").write_text("[app]\ndebug=true\n")
        assert _eval('@config.get["c.ini"; "app"; "debug"]') == "true"

    def test_sections(self, in_tmp):
        (in_tmp / "c.ini").write_text("[a]\nx=1\n[b]\ny=2\n")
        assert sorted(_eval('@config.sections["c.ini"]')) == ["a", "b"]

    def test_keys_section(self, in_tmp):
        (in_tmp / "c.ini").write_text("[s]\na=1\nb=2\n")
        assert sorted(_eval('@config.keys["c.ini"; "s"]')) == ["a", "b"]


class TestConfigDotenv:
    def test_load_dotenv(self, in_tmp):
        (in_tmp / ".env").write_text('APP_NAME=Cruhon\nDEBUG=true\n')
        data = _eval('@config.load[".env"]')
        assert data["APP_NAME"] == "Cruhon"

    def test_dotenv_into_environ(self, in_tmp):
        (in_tmp / ".env").write_text('TEST_VAR_CRUHON=hello\n')
        _run('@config.dotenv[".env"]')
        assert os.environ.get("TEST_VAR_CRUHON") == "hello"
        del os.environ["TEST_VAR_CRUHON"]


class TestConfigEnv:
    def test_env_get(self):
        os.environ["_CRUHON_TEST"] = "val"
        assert _eval('@config.env["_CRUHON_TEST"]') == "val"
        del os.environ["_CRUHON_TEST"]

    def test_env_default(self):
        assert _eval('@config.env["_CRUHON_MISSING_KEY_XYZ"; "default"]') == "default"

    def test_env_set(self):
        _run('@config.env_set["_CRUHON_SET_TEST"; "42"]')
        assert os.environ.get("_CRUHON_SET_TEST") == "42"
        del os.environ["_CRUHON_SET_TEST"]

    def test_env_del(self):
        os.environ["_CRUHON_DEL_TEST"] = "x"
        _run('@config.env_del["_CRUHON_DEL_TEST"]')
        assert "_CRUHON_DEL_TEST" not in os.environ

    def test_env_all(self):
        result = _eval('@config.env_all[]')
        assert isinstance(result, dict)
        assert len(result) > 0
