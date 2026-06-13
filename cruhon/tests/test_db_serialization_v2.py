"""
Tests for the second batch of @sqlite and @pickle additions.
"""
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
# @sqlite — short-hand queries
# ─────────────────────────────────────────────────────────────

class TestSqliteShorthand:
    def _db_with_data(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE users (id INT, name TEXT, score REAL)"]
@sqlite.execute[db; "INSERT INTO users VALUES (1, 'Alice', 9.5)"]
@sqlite.execute[db; "INSERT INTO users VALUES (2, 'Bob', 7.0)"]
@sqlite.execute[db; "INSERT INTO users VALUES (3, 'Alice2', 9.5)"]
"""
        return run(src)

    def test_all_rows(self):
        g = self._db_with_data()
        src = "@var[rows; @sqlite.all_rows[db; \"users\"]]"
        g = run(src, g)
        assert len(g["rows"]) == 3

    def test_find(self):
        g = self._db_with_data()
        src = "@var[rows; @sqlite.find[db; \"users\"; \"id\"; 1]]"
        g = run(src, g)
        assert len(g["rows"]) == 1
        assert g["rows"][0][1] == "Alice"

    def test_find_one(self):
        g = self._db_with_data()
        src = "@var[row; @sqlite.find_one[db; \"users\"; \"id\"; 2]]"
        g = run(src, g)
        assert g["row"][1] == "Bob"

    def test_find_one_missing(self):
        g = self._db_with_data()
        src = "@var[row; @sqlite.find_one[db; \"users\"; \"id\"; 99]]"
        g = run(src, g)
        assert g["row"] is None

    def test_exists_true(self):
        g = self._db_with_data()
        src = "@var[ok; @sqlite.exists[db; \"SELECT 1 FROM users WHERE id = 1\"]]"
        g = run(src, g)
        assert g["ok"] is True

    def test_exists_false(self):
        g = self._db_with_data()
        src = "@var[ok; @sqlite.exists[db; \"SELECT 1 FROM users WHERE id = 999\"]]"
        g = run(src, g)
        assert g["ok"] is False

    def test_exists_parameterized(self):
        g = self._db_with_data()
        src = "@var[ok; @sqlite.exists[db; \"SELECT 1 FROM users WHERE name = ?\"; (\"Alice\",)]]"
        g = run(src, g)
        assert g["ok"] is True

    def test_to_dicts(self):
        g = self._db_with_data()
        src = "@var[rows; @sqlite.to_dicts[db; \"SELECT * FROM users WHERE id = 1\"]]"
        g = run(src, g)
        assert g["rows"][0]["name"] == "Alice"

    def test_search(self):
        g = self._db_with_data()
        src = "@var[rows; @sqlite.search[db; \"users\"; \"name\"; \"Alice\"]]"
        g = run(src, g)
        assert len(g["rows"]) == 2

    def test_delete_many(self):
        g = self._db_with_data()
        src = "@sqlite.delete_many[db; \"users\"; \"id\"; [1, 2]]"
        g = run(src, g)
        src2 = "@var[n; @sqlite.count[db; \"users\"]]"
        g = run(src2, g)
        assert g["n"] == 1


class TestSqliteAggregates:
    def _db(self):
        return run("""
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x REAL)"]
@sqlite.execute[db; "INSERT INTO t VALUES (10)"]
@sqlite.execute[db; "INSERT INTO t VALUES (20)"]
@sqlite.execute[db; "INSERT INTO t VALUES (30)"]
""")

    def test_sum(self):
        g = self._db()
        g = run("@var[s; @sqlite.sum[db; \"t\"; \"x\"]]", g)
        assert g["s"] == 60.0

    def test_avg(self):
        g = self._db()
        g = run("@var[a; @sqlite.avg[db; \"t\"; \"x\"]]", g)
        assert g["a"] == 20.0

    def test_min_val(self):
        g = self._db()
        g = run("@var[m; @sqlite.min_val[db; \"t\"; \"x\"]]", g)
        assert g["m"] == 10.0

    def test_max_val(self):
        g = self._db()
        g = run("@var[m; @sqlite.max_val[db; \"t\"; \"x\"]]", g)
        assert g["m"] == 30.0


class TestSqliteSavepoints:
    def test_savepoint_and_rollback_to(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1)"]
@sqlite.savepoint[db; "sp1"]
@sqlite.execute[db; "INSERT INTO t VALUES (2)"]
@sqlite.rollback_to[db; "sp1"]
@var[n; @sqlite.count[db; "t"]]
"""
        g = run(src)
        assert g["n"] == 1

    def test_savepoint_and_release(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.savepoint[db; "sp1"]
@sqlite.execute[db; "INSERT INTO t VALUES (99)"]
@sqlite.release[db; "sp1"]
@var[n; @sqlite.count[db; "t"]]
"""
        g = run(src)
        assert g["n"] == 1


class TestSqliteConfiguration:
    def test_wal_mode(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@var[mode; @sqlite.wal_mode[db]]
"""
        g = run(src)
        assert g["mode"] in ("wal", "memory")

    def test_foreign_keys(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.foreign_keys[db]
"""
        run(src)  # no error = success

    def test_user_version_get_and_set(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.user_version[db; 42]
@var[v; @sqlite.user_version[db]]
"""
        g = run(src)
        assert g["v"] == 42

    def test_page_size(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@var[ps; @sqlite.page_size[db]]
"""
        g = run(src)
        assert isinstance(g["ps"], int)
        assert g["ps"] > 0

    def test_page_count(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@var[pc; @sqlite.page_count[db]]
"""
        g = run(src)
        assert isinstance(g["pc"], int)

    def test_views(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.execute[db; "CREATE VIEW v AS SELECT * FROM t"]
@var[vs; @sqlite.views[db]]
"""
        g = run(src)
        assert "v" in g["vs"]


class TestSqliteImportExport:
    def test_export_csv(self, tmp_path):
        csv_path = str(tmp_path / "out.csv")
        src = f"""
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id INT, name TEXT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1, 'Alice')"]
@sqlite.execute[db; "INSERT INTO t VALUES (2, 'Bob')"]
@sqlite.export_csv[db; "t"; "{csv_path}"]
"""
        run(src)
        import csv
        with open(csv_path, newline="") as f:
            rows = list(csv.reader(f))
        assert rows[0] == ["id", "name"]
        assert rows[1] == ["1", "Alice"]

    def test_import_csv(self, tmp_path):
        csv_path = str(tmp_path / "in.csv")
        import csv
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "name"])
            w.writeheader()
            w.writerows([{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}])
        src = f"""
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id TEXT, name TEXT)"]
@sqlite.import_csv[db; "t"; "{csv_path}"]
@var[n; @sqlite.count[db; "t"]]
"""
        g = run(src)
        assert g["n"] == 2

    def test_export_json(self, tmp_path):
        json_path = str(tmp_path / "out.json")
        src = f"""
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id INT, name TEXT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1, 'Alice')"]
@sqlite.export_json[db; "t"; "{json_path}"]
"""
        run(src)
        import json
        with open(json_path) as f:
            data = json.load(f)
        assert data[0]["name"] == "Alice"

    def test_roundtrip_csv(self, tmp_path):
        csv_path = str(tmp_path / "data.csv")
        src = f"""
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id INT, val TEXT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1, 'hello')"]
@sqlite.execute[db; "INSERT INTO t VALUES (2, 'world')"]
@sqlite.export_csv[db; "t"; "{csv_path}"]
@var[db2; @sqlite.connect[":memory:"]]
@sqlite.execute[db2; "CREATE TABLE t (id TEXT, val TEXT)"]
@sqlite.import_csv[db2; "t"; "{csv_path}"]
@var[n; @sqlite.count[db2; "t"]]
"""
        g = run(src)
        assert g["n"] == 2


# ─────────────────────────────────────────────────────────────
# @pickle — list file helpers
# ─────────────────────────────────────────────────────────────

class TestPickleListHelpers:
    def test_append_to_creates_list(self, tmp_path):
        path = str(tmp_path / "list.pkl")
        src = f"""
@pickle.append_to["{path}"; "first"]
@pickle.append_to["{path}"; "second"]
@pickle.append_to["{path}"; "third"]
@var[lst; @pickle.load_list["{path}"]]
"""
        g = run(src)
        assert g["lst"] == ["first", "second", "third"]

    def test_load_list_missing_file(self, tmp_path):
        path = str(tmp_path / "nonexistent.pkl")
        src = f'@var[lst; @pickle.load_list["{path}"]]'
        g = run(src)
        assert g["lst"] == []

    def test_append_to_mixed_types(self, tmp_path):
        path = str(tmp_path / "list.pkl")
        src = f"""
@pickle.append_to["{path}"; 42]
@pickle.append_to["{path}"; {{"key": "val"}}]
@pickle.append_to["{path}"; [1, 2, 3]]
@var[lst; @pickle.load_list["{path}"]]
"""
        g = run(src)
        assert g["lst"][0] == 42
        assert g["lst"][1] == {"key": "val"}
        assert g["lst"][2] == [1, 2, 3]

    def test_compress_and_decompress(self):
        src = """
@var[data; list(range(100))]
@var[compressed; @pickle.compress[data]]
@var[restored; @pickle.decompress[compressed]]
"""
        g = run(src)
        assert g["restored"] == list(range(100))
        assert isinstance(g["compressed"], bytes)

    def test_compress_is_bytes(self):
        src = """
@var[data; {"key": "value", "nums": [1, 2, 3]}}]
@var[c; @pickle.compress[data]]
"""
        g = run("""
@var[data; {"key": "value"}]
@var[c; @pickle.compress[data]]
""")
        assert isinstance(g["c"], bytes)
