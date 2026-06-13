"""
Tests for Database & Serialization namespaces:
  @sqlite, @pickle, @shelve, @plist
"""
import os
import tempfile
from pathlib import Path

import pytest

from cruhon.core.transpiler import Transpiler
from cruhon.core.parser import Parser


def transpile(src: str) -> str:
    return Transpiler().transpile(Parser().parse(src))


def run(src: str, globs: dict = None) -> dict:
    code = transpile(src)
    g = globs or {}
    exec(compile(code, "<test>", "exec"), g)
    return g


# ─────────────────────────────────────────────────────────────
# @sqlite
# ─────────────────────────────────────────────────────────────

class TestSqliteTranspile:
    def test_connect(self):
        r = transpile("@var[db; @sqlite.connect[\":memory:\"]]")
        assert "sqlite3" in r
        assert "connect" in r
        assert '":memory:"' in r

    def test_fetchall(self):
        r = transpile("@var[rows; @sqlite.fetchall[db; \"SELECT 1\"]]")
        assert "fetchall" in r

    def test_fetchone(self):
        r = transpile("@var[row; @sqlite.fetchone[db; \"SELECT 1\"]]")
        assert "fetchone" in r

    def test_fetchmany(self):
        r = transpile("@var[rows; @sqlite.fetchmany[db; \"SELECT 1\"; 5]]")
        assert "fetchmany" in r

    def test_execute(self):
        r = transpile("@sqlite.execute[db; \"CREATE TABLE t (x INT)\"]")
        assert "execute" in r

    def test_commit(self):
        r = transpile("@sqlite.commit[db]")
        assert "commit" in r

    def test_close(self):
        r = transpile("@sqlite.close[db]")
        assert "close" in r

    def test_insert(self):
        r = transpile("@sqlite.insert[db; \"users\"; row]")
        assert "INSERT" in r

    def test_delete(self):
        r = transpile("@sqlite.delete[db; \"users\"; \"id\"; 1]")
        assert "DELETE" in r

    def test_tables(self):
        r = transpile("@var[t; @sqlite.tables[db]]")
        assert "sqlite_master" in r

    def test_columns(self):
        r = transpile("@var[cols; @sqlite.columns[db; \"users\"]]")
        assert "PRAGMA" in r

    def test_count(self):
        r = transpile("@var[n; @sqlite.count[db; \"users\"]]")
        assert "COUNT" in r

    def test_query_oneshot(self):
        r = transpile("@var[rows; @sqlite.query[\":memory:\"; \"SELECT 1\"]]")
        assert "connect" in r
        assert "fetchall" in r

    def test_run_oneshot(self):
        r = transpile("@sqlite.run[\"db.sqlite3\"; \"CREATE TABLE t (x INT)\"]")
        assert "commit" in r

    def test_as_dict(self):
        r = transpile("@sqlite.as_dict[db]")
        assert "row_factory" in r


class TestSqliteRuntime:
    def test_connect_memory(self):
        g = run("@var[db; @sqlite.connect[\":memory:\"]]")
        import sqlite3
        assert isinstance(g["db"], sqlite3.Connection)

    def test_create_and_fetchall(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id INT, name TEXT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1, 'Alice')"]
@sqlite.execute[db; "INSERT INTO t VALUES (2, 'Bob')"]
@var[rows; @sqlite.fetchall[db; "SELECT * FROM t"]]
@sqlite.close[db]
"""
        g = run(src)
        assert len(g["rows"]) == 2

    def test_fetchone(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (42)"]
@var[row; @sqlite.fetchone[db; "SELECT x FROM t"]]
"""
        g = run(src)
        assert g["row"][0] == 42

    def test_parameterized_query(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id INT, name TEXT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (?, ?)"; (1, "Alice")]
@var[rows; @sqlite.fetchall[db; "SELECT * FROM t WHERE id = ?"; (1,)]]
"""
        g = run(src)
        assert len(g["rows"]) == 1

    def test_insert_from_dict(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE users (id INT, name TEXT)"]
@var[row; {"id": 1, "name": "Alice"}]
@sqlite.insert[db; "users"; row]
@var[rows; @sqlite.fetchall[db; "SELECT * FROM users"]]
"""
        g = run(src)
        assert len(g["rows"]) == 1

    def test_tables(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE alpha (x INT)"]
@sqlite.execute[db; "CREATE TABLE beta (y TEXT)"]
@var[tbls; @sqlite.tables[db]]
"""
        g = run(src)
        assert sorted(g["tbls"]) == ["alpha", "beta"]

    def test_columns(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id INT, name TEXT, score REAL)"]
@var[cols; @sqlite.columns[db; "t"]]
"""
        g = run(src)
        assert g["cols"] == ["id", "name", "score"]

    def test_count(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1)"]
@sqlite.execute[db; "INSERT INTO t VALUES (2)"]
@var[n; @sqlite.count[db; "t"]]
"""
        g = run(src)
        assert g["n"] == 2

    def test_delete(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id INT, name TEXT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1, 'Alice')"]
@sqlite.execute[db; "INSERT INTO t VALUES (2, 'Bob')"]
@sqlite.delete[db; "t"; "id"; 1]
@var[rows; @sqlite.fetchall[db; "SELECT * FROM t"]]
"""
        g = run(src)
        assert len(g["rows"]) == 1

    def test_query_oneshot(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE t (x INT)")
        conn.execute("INSERT INTO t VALUES (99)")
        conn.commit()
        conn.close()

        src = f'@var[rows; @sqlite.query["{db_path}"; "SELECT * FROM t"]]'
        g = run(src)
        assert g["rows"][0][0] == 99

    def test_commit_persists(self, tmp_path):
        db_path = str(tmp_path / "persist.db")
        src1 = f"""
@var[db; @sqlite.connect["{db_path}"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (7)"]
@sqlite.commit[db]
@sqlite.close[db]
"""
        run(src1)
        src2 = f'@var[rows; @sqlite.query["{db_path}"; "SELECT * FROM t"]]'
        g = run(src2)
        assert g["rows"][0][0] == 7

    def test_as_dict_rows(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.as_dict[db]
@sqlite.execute[db; "CREATE TABLE t (id INT, name TEXT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1, 'Alice')"]
@var[rows; @sqlite.fetchall[db; "SELECT * FROM t"]]
"""
        g = run(src)
        row = g["rows"][0]
        assert row["name"] == "Alice"


# ─────────────────────────────────────────────────────────────
# @pickle
# ─────────────────────────────────────────────────────────────

class TestPickleTranspile:
    def test_dumps(self):
        r = transpile("@var[b; @pickle.dumps[obj]]")
        assert "pickle" in r
        assert "dumps" in r

    def test_loads(self):
        r = transpile("@var[obj; @pickle.loads[data]]")
        assert "pickle" in r
        assert "loads" in r

    def test_save(self):
        r = transpile("@pickle.save[\"file.pkl\"; obj]")
        assert "pickle" in r

    def test_load(self):
        r = transpile("@var[obj; @pickle.load[\"file.pkl\"]]")
        assert "pickle" in r

    def test_copy(self):
        r = transpile("@var[obj2; @pickle.copy[obj]]")
        assert "pickle" in r

    def test_dumps_proto(self):
        r = transpile("@var[b; @pickle.dumps_proto[obj; 4]]")
        assert "protocol" in r


class TestPickleRuntime:
    def test_roundtrip_basic(self):
        src = """
@var[original; {"key": [1, 2, 3], "name": "Alice"}]
@var[data; @pickle.dumps[original]]
@var[restored; @pickle.loads[data]]
"""
        g = run(src)
        assert g["restored"] == {"key": [1, 2, 3], "name": "Alice"}

    def test_roundtrip_list(self):
        src = """
@var[lst; [10, 20, 30]]
@var[b; @pickle.dumps[lst]]
@var[lst2; @pickle.loads[b]]
"""
        g = run(src)
        assert g["lst2"] == [10, 20, 30]

    def test_copy(self):
        src = """
@var[orig; [1, 2, 3]]
@var[copied; @pickle.copy[orig]]
"""
        g = run(src)
        assert g["copied"] == [1, 2, 3]
        assert g["copied"] is not g["orig"]

    def test_save_and_load(self, tmp_path):
        pkl_path = str(tmp_path / "data.pkl")
        src1 = f"""
@var[data; {{"x": 42, "y": [1, 2]}}]
@pickle.save["{pkl_path}"; data]
"""
        run(src1)
        src2 = f'@var[loaded; @pickle.load["{pkl_path}"]]'
        g = run(src2)
        assert g["loaded"] == {"x": 42, "y": [1, 2]}

    def test_dumps_is_bytes(self):
        src = """
@var[data; [1, 2, 3]]
@var[b; @pickle.dumps[data]]
"""
        g = run(src)
        assert isinstance(g["b"], bytes)

    def test_protocol(self):
        src = """
@var[data; {"a": 1}]
@var[b; @pickle.dumps_proto[data; 4]]
@var[restored; @pickle.loads[b]]
"""
        g = run(src)
        assert g["restored"] == {"a": 1}


# ─────────────────────────────────────────────────────────────
# @shelve
# ─────────────────────────────────────────────────────────────

class TestShelveTranspile:
    def test_get(self):
        r = transpile("@var[v; @shelve.get[\"db\"; \"key\"]]")
        assert "shelve" in r

    def test_set(self):
        r = transpile("@shelve.set[\"db\"; \"key\"; value]")
        assert "shelve" in r

    def test_has(self):
        r = transpile("@var[ok; @shelve.has[\"db\"; \"key\"]]")
        assert "shelve" in r

    def test_keys(self):
        r = transpile("@var[ks; @shelve.keys[\"db\"]]")
        assert "shelve" in r

    def test_all(self):
        r = transpile("@var[d; @shelve.all[\"db\"]]")
        assert "shelve" in r

    def test_count(self):
        r = transpile("@var[n; @shelve.count[\"db\"]]")
        assert "shelve" in r


class TestShelveRuntime:
    def test_set_and_get(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.set["{db}"; "name"; "Alice"]
@var[v; @shelve.get["{db}"; "name"]]
"""
        g = run(src)
        assert g["v"] == "Alice"

    def test_get_default(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f'@var[v; @shelve.get["{db}"; "missing"; "default_val"]]'
        g = run(src)
        assert g["v"] == "default_val"

    def test_has(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.set["{db}"; "x"; 1]
@var[yes; @shelve.has["{db}"; "x"]]
@var[no; @shelve.has["{db}"; "y"]]
"""
        g = run(src)
        assert g["yes"] is True
        assert g["no"] is False

    def test_delete(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.set["{db}"; "k"; 99]
@shelve.delete["{db}"; "k"]
@var[v; @shelve.get["{db}"; "k"; None]]
"""
        g = run(src)
        assert g["v"] is None

    def test_keys(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.set["{db}"; "a"; 1]
@shelve.set["{db}"; "b"; 2]
@var[ks; @shelve.keys["{db}"]]
"""
        g = run(src)
        assert sorted(g["ks"]) == ["a", "b"]

    def test_all(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.set["{db}"; "x"; 10]
@shelve.set["{db}"; "y"; 20]
@var[d; @shelve.all["{db}"]]
"""
        g = run(src)
        assert g["d"] == {"x": 10, "y": 20}

    def test_clear(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.set["{db}"; "a"; 1]
@shelve.set["{db}"; "b"; 2]
@shelve.clear["{db}"]
@var[n; @shelve.count["{db}"]]
"""
        g = run(src)
        assert g["n"] == 0

    def test_update(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@var[d; {{"p": 1, "q": 2}}]
@shelve.update["{db}"; d]
@var[v; @shelve.get["{db}"; "p"]]
"""
        g = run(src)
        assert g["v"] == 1

    def test_count(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.set["{db}"; "a"; 1]
@shelve.set["{db}"; "b"; 2]
@shelve.set["{db}"; "c"; 3]
@var[n; @shelve.count["{db}"]]
"""
        g = run(src)
        assert g["n"] == 3

    def test_stores_complex_objects(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@var[data; {{"items": [1, 2, 3], "meta": {{"created": "today"}}}}]
@shelve.set["{db}"; "obj"; data]
@var[loaded; @shelve.get["{db}"; "obj"]]
"""
        g = run(src)
        assert g["loaded"]["items"] == [1, 2, 3]


# ─────────────────────────────────────────────────────────────
# @plist
# ─────────────────────────────────────────────────────────────

class TestPlistTranspile:
    def test_loads(self):
        r = transpile("@var[d; @plist.loads[text]]")
        assert "plistlib" in r

    def test_dumps(self):
        r = transpile("@var[s; @plist.dumps[data]]")
        assert "plistlib" in r

    def test_load(self):
        r = transpile("@var[d; @plist.load[\"file.plist\"]]")
        assert "plistlib" in r

    def test_save(self):
        r = transpile("@plist.save[\"file.plist\"; data]")
        assert "plistlib" in r

    def test_get(self):
        r = transpile("@var[v; @plist.get[data; \"key\"]]")
        assert "get" in r

    def test_to_json(self):
        r = transpile("@var[j; @plist.to_json[data]]")
        assert "json" in r


class TestPlistRuntime:
    def test_dumps_and_loads(self):
        src = """
@var[data; {"name": "Alice", "age": 30}]
@var[text; @plist.dumps[data]]
@var[restored; @plist.loads[text]]
"""
        g = run(src)
        assert g["restored"]["name"] == "Alice"
        assert g["restored"]["age"] == 30

    def test_dumps_is_xml(self):
        src = """
@var[data; {"key": "value"}]
@var[text; @plist.dumps[data]]
"""
        g = run(src)
        assert "<?xml" in g["text"] or "plist" in g["text"]

    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "test.plist")
        src1 = f"""
@var[data; {{"score": 100, "name": "Bob"}}]
@plist.save["{path}"; data]
"""
        run(src1)
        src2 = f'@var[d; @plist.load["{path}"]]'
        g = run(src2)
        assert g["d"]["score"] == 100
        assert g["d"]["name"] == "Bob"

    def test_get(self):
        src = """
@var[data; {"name": "Alice", "age": 30}]
@var[name; @plist.get[data; "name"]]
@var[missing; @plist.get[data; "x"; "default"]]
"""
        g = run(src)
        assert g["name"] == "Alice"
        assert g["missing"] == "default"

    def test_to_json(self):
        src = """
@var[data; {"key": "val"}]
@var[j; @plist.to_json[data]]
"""
        g = run(src)
        import json
        assert json.loads(g["j"]) == {"key": "val"}

    def test_loads_bytes(self):
        import plistlib
        data = {"x": 1}
        raw = plistlib.dumps(data)
        src = f"@var[d; @plist.loads[{raw!r}]]"
        g = run(src)
        assert g["d"]["x"] == 1
