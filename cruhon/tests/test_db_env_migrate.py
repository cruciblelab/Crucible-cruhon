"""
Tests for cruhon-db v2 additions:
  @db.connect_env  ·  @db.dsn_safe  ·  @db.migrate  ·  @db.seed
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core import mod_loader
from cruhon.core.runner import run_source


@pytest.fixture(scope="module", autouse=True)
def _load_db_mod():
    mod_path = Path(__file__).parent.parent.parent / "mods" / "cruhon-db"
    mod_loader.load_mod_from_path(mod_path)


def _mask_dsn(url):
    from importlib import import_module
    m = import_module("__init__") if False else None
    # Reach the helper directly through the loaded module object.
    import cruhon  # noqa
    return None


# ─────────────────────────────────────────────────────────────
# @db.dsn_safe — password masking
# ─────────────────────────────────────────────────────────────

class TestDsnMask:
    def test_mask_helper(self):
        # Pull the module the loader imported and call its helper directly.
        import sys
        mod = next(m for n, m in sys.modules.items()
                   if getattr(m, "_mask_dsn", None) and getattr(m, "_parse_dsn", None))
        assert mod._mask_dsn("postgres://user:secret@host:5432/db") == \
            "postgres://user:****@host:5432/db"
        assert mod._mask_dsn("mysql://root:p4ss@127.0.0.1/app") == \
            "mysql://root:****@127.0.0.1/app"
        # sqlite path → unchanged (no credentials)
        assert mod._mask_dsn("sqlite:///data.db") == "sqlite:///data.db"

    def test_dsn_safe_command(self, tmp_path):
        db = tmp_path / "x.db"
        src = (
            f'@db.connect["sqlite:///{db}"]\n'
            f'@var[safe; @db.dsn_safe[]]\n'
            f'@print[{{safe}}]'
        )
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_source(src)
        assert str(db) in buf.getvalue()


# ─────────────────────────────────────────────────────────────
# @db.connect_env — DSN from an environment variable
# ─────────────────────────────────────────────────────────────

class TestConnectEnv:
    def test_connect_env_default_var(self, tmp_path, monkeypatch):
        db = tmp_path / "env.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
        src = (
            '@db.connect_env[]\n'
            '@db.exec["CREATE TABLE t (id INTEGER PRIMARY KEY, n TEXT)"]\n'
            '@db.insert["t"; {"n": "ok"}]\n'
            '@var[rows; @db.query["SELECT * FROM t"]]\n'
            '@print[{len(rows)}]'
        )
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_source(src)
        assert buf.getvalue().strip() == "1"

    def test_connect_env_custom_var(self, tmp_path, monkeypatch):
        db = tmp_path / "custom.db"
        monkeypatch.setenv("MY_DB", f"sqlite:///{db}")
        src = (
            '@db.connect_env["MY_DB"]\n'
            '@var[ok; @db.ping[]]\n'
            '@print[{ok}]'
        )
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_source(src)
        assert buf.getvalue().strip() == "True"

    def test_connect_env_missing_raises(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from cruhon.core.runner import RunError
        with pytest.raises((RuntimeError, RunError)):
            run_source('@db.connect_env[]')


# ─────────────────────────────────────────────────────────────
# @db.migrate — idempotent SQL migrations
# ─────────────────────────────────────────────────────────────

class TestMigrate:
    def test_migrate_applies_in_order(self, tmp_path):
        mig = tmp_path / "migrations"
        mig.mkdir()
        (mig / "001_users.sql").write_text(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);"
        )
        (mig / "002_seed.sql").write_text(
            "INSERT INTO users (name) VALUES ('alice');"
        )
        db = tmp_path / "m.db"
        src = (
            f'@db.connect["sqlite:///{db}"]\n'
            f'@var[applied; @db.migrate["{mig}"]]\n'
            f'@var[users; @db.query["SELECT * FROM users"]]\n'
            f'@print[{{len(applied)}}|{{len(users)}}]'
        )
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_source(src)
        assert buf.getvalue().strip() == "2|1"

    def test_migrate_is_idempotent(self, tmp_path):
        mig = tmp_path / "migrations"
        mig.mkdir()
        (mig / "001_init.sql").write_text(
            "CREATE TABLE t (id INTEGER PRIMARY KEY);"
        )
        db = tmp_path / "idem.db"
        base = f'@db.connect["sqlite:///{db}"]\n'
        # First run applies one file.
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_source(base + f'@var[a; @db.migrate["{mig}"]]\n@print[{{len(a)}}]')
        assert buf.getvalue().strip() == "1"
        # Second run applies nothing (already tracked).
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_source(base + f'@var[a; @db.migrate["{mig}"]]\n@print[{{len(a)}}]')
        assert buf.getvalue().strip() == "0"


# ─────────────────────────────────────────────────────────────
# @db.seed — bulk load from JSON / CSV
# ─────────────────────────────────────────────────────────────

class TestSeed:
    def test_seed_json(self, tmp_path):
        data = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}, {"id": 3, "name": "c"}]
        f = tmp_path / "people.json"
        f.write_text(json.dumps(data))
        db = tmp_path / "s.db"
        src = (
            f'@db.connect["sqlite:///{db}"]\n'
            f'@db.exec["CREATE TABLE people (id INTEGER, name TEXT)"]\n'
            f'@var[n; @db.seed["people"; "{f}"]]\n'
            f'@var[rows; @db.query["SELECT * FROM people ORDER BY id"]]\n'
            f'@print[{{n}}|{{rows[0]["name"]}}|{{rows[2]["name"]}}]'
        )
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_source(src)
        assert buf.getvalue().strip() == "3|a|c"

    def test_seed_csv(self, tmp_path):
        f = tmp_path / "cities.csv"
        f.write_text("id,name\n1,Paris\n2,Tokyo\n")
        db = tmp_path / "csv.db"
        src = (
            f'@db.connect["sqlite:///{db}"]\n'
            f'@db.exec["CREATE TABLE cities (id TEXT, name TEXT)"]\n'
            f'@var[n; @db.seed["cities"; "{f}"]]\n'
            f'@var[rows; @db.query["SELECT * FROM cities ORDER BY id"]]\n'
            f'@print[{{n}}|{{rows[1]["name"]}}]'
        )
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_source(src)
        assert buf.getvalue().strip() == "2|Tokyo"
