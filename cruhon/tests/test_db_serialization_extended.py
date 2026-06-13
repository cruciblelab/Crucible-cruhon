"""
Extended tests for the expanded @sqlite, @pickle, @shelve, @plist namespaces.
"""
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
# @sqlite — new methods
# ─────────────────────────────────────────────────────────────

class TestSqliteExtended:
    def test_rollback(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1)"]
@sqlite.rollback[db]
@var[rows; @sqlite.fetchall[db; "SELECT * FROM t"]]
"""
        g = run(src)
        assert g["rows"] == []

    def test_begin_and_commit(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.begin[db]
@sqlite.execute[db; "INSERT INTO t VALUES (42)"]
@sqlite.commit[db]
@var[rows; @sqlite.fetchall[db; "SELECT * FROM t"]]
"""
        g = run(src)
        assert len(g["rows"]) == 1

    def test_in_transaction(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "BEGIN"]
@var[flag; @sqlite.in_transaction[db]]
"""
        g = run(src)
        assert g["flag"] is True

    def test_executemany(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.executemany[db; "INSERT INTO t VALUES (?)"; [(1,), (2,), (3,)]]
@var[n; @sqlite.count[db; "t"]]
"""
        g = run(src)
        assert g["n"] == 3

    def test_executescript(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.executescript[db; "CREATE TABLE a (x INT); CREATE TABLE b (y TEXT);"]
@var[tbls; @sqlite.tables[db]]
"""
        g = run(src)
        assert sorted(g["tbls"]) == ["a", "b"]

    def test_scalar(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (7)"]
@var[val; @sqlite.scalar[db; "SELECT x FROM t"]]
"""
        g = run(src)
        assert g["val"] == 7

    def test_scalar_parameterized(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (99)"]
@var[val; @sqlite.scalar[db; "SELECT x FROM t WHERE x = ?"; (99,)]]
"""
        g = run(src)
        assert g["val"] == 99

    def test_query_one(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE t (x INT)")
        conn.execute("INSERT INTO t VALUES (55)")
        conn.commit()
        conn.close()
        src = f'@var[row; @sqlite.query_one["{db_path}"; "SELECT x FROM t"]]'
        g = run(src)
        assert g["row"][0] == 55

    def test_insert_many(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id INT, name TEXT)"]
@var[rows; [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]]
@sqlite.insert_many[db; "t"; rows]
@var[n; @sqlite.count[db; "t"]]
"""
        g = run(src)
        assert g["n"] == 2

    def test_upsert(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id INT PRIMARY KEY, name TEXT)"]
@sqlite.insert[db; "t"; {"id": 1, "name": "Alice"}]
@sqlite.upsert[db; "t"; {"id": 1, "name": "Alice Updated"}; "id"]
@var[n; @sqlite.count[db; "t"]]
@var[row; @sqlite.fetchone[db; "SELECT name FROM t WHERE id = 1"]]
"""
        g = run(src)
        assert g["n"] == 1
        assert g["row"][0] == "Alice Updated"

    def test_truncate(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1)"]
@sqlite.execute[db; "INSERT INTO t VALUES (2)"]
@sqlite.truncate[db; "t"]
@var[n; @sqlite.count[db; "t"]]
"""
        g = run(src)
        assert g["n"] == 0

    def test_create_table(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@var[schema; {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "score": "REAL"}]
@sqlite.create_table[db; "users"; schema]
@var[exists; @sqlite.table_exists[db; "users"]]
"""
        g = run(src)
        assert g["exists"] is True

    def test_drop_table(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.drop_table[db; "t"]
@var[exists; @sqlite.table_exists[db; "t"]]
"""
        g = run(src)
        assert g["exists"] is False

    def test_table_exists_false(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@var[exists; @sqlite.table_exists[db; "nonexistent"]]
"""
        g = run(src)
        assert g["exists"] is False

    def test_column_types(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id INTEGER, name TEXT, score REAL)"]
@var[types; @sqlite.column_types[db; "t"]]
"""
        g = run(src)
        assert g["types"]["name"] == "TEXT"
        assert g["types"]["score"] == "REAL"

    def test_index_create_and_drop(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id INT, name TEXT)"]
@sqlite.index_create[db; "t"; "name"]
@sqlite.index_drop[db; "idx_t_name"]
"""
        g = run(src)  # no error = success

    def test_as_dicts(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.as_dict[db]
@sqlite.execute[db; "CREATE TABLE t (id INT, name TEXT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1, 'Alice')"]
@var[rows; @sqlite.fetchall[db; "SELECT * FROM t"]]
@var[dicts; @sqlite.as_dicts[rows]]
"""
        g = run(src)
        assert g["dicts"][0]["name"] == "Alice"

    def test_last_id(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"]
@sqlite.execute[db; "INSERT INTO t (name) VALUES ('Alice')"]
@var[lid; @sqlite.last_id[db]]
"""
        g = run(src)
        assert g["lid"] == 1

    def test_changes(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1)"]
@sqlite.execute[db; "INSERT INTO t VALUES (2)"]
@sqlite.execute[db; "UPDATE t SET x = 99"]
@var[n; @sqlite.changes[db]]
"""
        g = run(src)
        assert g["n"] == 2

    def test_vacuum(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.vacuum[db]
"""
        g = run(src)  # no error = success

    def test_integrity_check(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@var[result; @sqlite.integrity_check[db]]
"""
        g = run(src)
        assert g["result"] == "ok"

    def test_pragma_get(self):
        src = """
@var[db; @sqlite.connect[":memory:"]]
@var[v; @sqlite.pragma[db; "journal_mode"]]
"""
        g = run(src)
        assert isinstance(g["v"], str)

    def test_backup(self, tmp_path):
        src = f"""
@var[db; @sqlite.connect[":memory:"]]
@sqlite.execute[db; "CREATE TABLE t (x INT)"]
@sqlite.execute[db; "INSERT INTO t VALUES (1)"]
@sqlite.commit[db]
@sqlite.backup[db; "{tmp_path / 'backup.db'}"]
"""
        run(src)
        import sqlite3
        conn = sqlite3.connect(str(tmp_path / "backup.db"))
        rows = conn.execute("SELECT * FROM t").fetchall()
        conn.close()
        assert rows[0][0] == 1


# ─────────────────────────────────────────────────────────────
# @pickle — new methods
# ─────────────────────────────────────────────────────────────

class TestPickleExtended:
    def test_save_gz_and_load_gz(self, tmp_path):
        path = str(tmp_path / "data.pkl.gz")
        src1 = f"""
@var[data; {{"x": [1, 2, 3], "y": "hello"}}]
@pickle.save_gz["{path}"; data]
"""
        run(src1)
        src2 = f'@var[loaded; @pickle.load_gz["{path}"]]'
        g = run(src2)
        assert g["loaded"] == {"x": [1, 2, 3], "y": "hello"}

    def test_to_base64_and_from_base64(self):
        src = """
@var[data; [10, 20, 30]]
@var[encoded; @pickle.to_base64[data]]
@var[decoded; @pickle.from_base64[encoded]]
"""
        g = run(src)
        assert g["decoded"] == [10, 20, 30]
        assert isinstance(g["encoded"], str)

    def test_to_hex_and_from_hex(self):
        src = """
@var[data; {"key": "val"}]
@var[h; @pickle.to_hex[data]]
@var[restored; @pickle.from_hex[h]]
"""
        g = run(src)
        assert g["restored"] == {"key": "val"}
        assert isinstance(g["h"], str)
        assert all(c in "0123456789abcdef" for c in g["h"])

    def test_is_pickle_true(self):
        src = """
@var[data; [1, 2, 3]]
@var[b; @pickle.dumps[data]]
@var[ok; @pickle.is_pickle[b]]
"""
        g = run(src)
        assert g["ok"] is True

    def test_is_pickle_false(self):
        src = """
@var[b; b"not pickle data"]
@var[ok; @pickle.is_pickle[b]]
"""
        g = run(src)
        assert g["ok"] is False

    def test_size(self):
        src = """
@var[data; [1, 2, 3, 4, 5]]
@var[n; @pickle.size[data]]
"""
        g = run(src)
        assert isinstance(g["n"], int)
        assert g["n"] > 0

    def test_protocol_detection(self):
        src = """
@var[data; {"x": 1}]
@var[b; @pickle.dumps_proto[data; 4]]
@var[proto; @pickle.protocol[b]]
"""
        g = run(src)
        assert g["proto"] == 4

    def test_gz_smaller_than_plain(self, tmp_path):
        p_plain = str(tmp_path / "plain.pkl")
        p_gz = str(tmp_path / "compressed.pkl.gz")
        src = f"""
@var[data; list(range(1000))]
@pickle.save["{p_plain}"; data]
@pickle.save_gz["{p_gz}"; data]
"""
        run(src)
        import os
        assert os.path.getsize(p_gz) < os.path.getsize(p_plain)


# ─────────────────────────────────────────────────────────────
# @shelve — new methods
# ─────────────────────────────────────────────────────────────

class TestShelveExtended:
    def test_values(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.set["{db}"; "a"; 1]
@shelve.set["{db}"; "b"; 2]
@var[vals; @shelve.values["{db}"]]
"""
        g = run(src)
        assert sorted(g["vals"]) == [1, 2]

    def test_items(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.set["{db}"; "x"; 10]
@var[its; @shelve.items["{db}"]]
"""
        g = run(src)
        assert g["its"] == [("x", 10)]

    def test_pop(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.set["{db}"; "k"; 42]
@var[v; @shelve.pop["{db}"; "k"]]
@var[gone; @shelve.has["{db}"; "k"]]
"""
        g = run(src)
        assert g["v"] == 42
        assert g["gone"] is False

    def test_pop_default(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f'@var[v; @shelve.pop["{db}"; "missing"; "fallback"]]'
        g = run(src)
        assert g["v"] == "fallback"

    def test_setdefault_new(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@var[v; @shelve.setdefault["{db}"; "k"; 99]]
@var[v2; @shelve.get["{db}"; "k"]]
"""
        g = run(src)
        assert g["v"] == 99
        assert g["v2"] == 99

    def test_setdefault_existing(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.set["{db}"; "k"; 1]
@var[v; @shelve.setdefault["{db}"; "k"; 99]]
"""
        g = run(src)
        assert g["v"] == 1

    def test_rename(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.set["{db}"; "old"; "value"]
@shelve.rename["{db}"; "old"; "new"]
@var[v; @shelve.get["{db}"; "new"]]
@var[gone; @shelve.has["{db}"; "old"]]
"""
        g = run(src)
        assert g["v"] == "value"
        assert g["gone"] is False

    def test_increment(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.increment["{db}"; "counter"]
@shelve.increment["{db}"; "counter"]
@shelve.increment["{db}"; "counter"]
@var[n; @shelve.get["{db}"; "counter"]]
"""
        g = run(src)
        assert g["n"] == 3

    def test_increment_by_n(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@shelve.increment["{db}"; "score"; 10]
@shelve.increment["{db}"; "score"; 5]
@var[n; @shelve.get["{db}"; "score"]]
"""
        g = run(src)
        assert g["n"] == 15

    def test_sync_via_handle(self, tmp_path):
        db = str(tmp_path / "shelf")
        src = f"""
@var[s; @shelve.open["{db}"]]
@var[_ ; s.__setitem__("k", 123)]
@shelve.sync[s]
@shelve.close[s]
@var[v; @shelve.get["{db}"; "k"]]
"""
        g = run(src)
        assert g["v"] == 123


# ─────────────────────────────────────────────────────────────
# @plist — new methods
# ─────────────────────────────────────────────────────────────

class TestPlistExtended:
    def test_set(self):
        src = """
@var[d; {"a": 1}]
@var[d2; @plist.set[d; "b"; 2]]
"""
        g = run(src)
        assert g["d2"] == {"a": 1, "b": 2}
        assert "b" not in g["d"]

    def test_has(self):
        src = """
@var[d; {"x": 1}]
@var[yes; @plist.has[d; "x"]]
@var[no; @plist.has[d; "y"]]
"""
        g = run(src)
        assert g["yes"] is True
        assert g["no"] is False

    def test_keys(self):
        src = """
@var[d; {"a": 1, "b": 2}]
@var[ks; @plist.keys[d]]
"""
        g = run(src)
        assert sorted(g["ks"]) == ["a", "b"]

    def test_values(self):
        src = """
@var[d; {"x": 10, "y": 20}]
@var[vs; @plist.values[d]]
"""
        g = run(src)
        assert sorted(g["vs"]) == [10, 20]

    def test_items(self):
        src = """
@var[d; {"k": "v"}]
@var[its; @plist.items[d]]
"""
        g = run(src)
        assert g["its"] == [("k", "v")]

    def test_merge(self):
        src = """
@var[d1; {"a": 1, "b": 2}]
@var[d2; {"b": 99, "c": 3}]
@var[merged; @plist.merge[d1; d2]]
"""
        g = run(src)
        assert g["merged"] == {"a": 1, "b": 99, "c": 3}

    def test_remove(self):
        src = """
@var[d; {"a": 1, "b": 2, "c": 3}]
@var[d2; @plist.remove[d; "b"]]
"""
        g = run(src)
        assert "b" not in g["d2"]
        assert g["d2"] == {"a": 1, "c": 3}

    def test_to_dict(self):
        src = """
@var[d; {"name": "Alice", "scores": [10, 20]}]
@var[plain; @plist.to_dict[d]]
"""
        g = run(src)
        assert g["plain"] == {"name": "Alice", "scores": [10, 20]}

    def test_save_binary_and_load_binary(self, tmp_path):
        path = str(tmp_path / "test.plist")
        src1 = f"""
@var[data; {{"name": "Alice", "score": 100}}]
@plist.save_binary["{path}"; data]
"""
        run(src1)
        src2 = f'@var[d; @plist.load_binary["{path}"]]'
        g = run(src2)
        assert g["d"]["name"] == "Alice"

    def test_dumps_binary_and_loads_binary(self):
        src = """
@var[data; {"x": 42, "y": [1, 2, 3]}]
@var[raw; @plist.dumps_binary[data]]
@var[restored; @plist.loads_binary[raw]]
"""
        g = run(src)
        assert g["restored"]["x"] == 42
        assert isinstance(g["raw"], bytes)

    def test_fmt_xml(self, tmp_path):
        path = str(tmp_path / "test.plist")
        src1 = f'@plist.save["{path}"; {{"k": "v"}}]'
        run(src1)
        src2 = f'@var[f; @plist.fmt["{path}"]]'
        g = run(src2)
        assert g["f"] == "xml"

    def test_fmt_binary(self, tmp_path):
        path = str(tmp_path / "test.plist")
        src1 = f'@plist.save_binary["{path}"; {{"k": "v"}}]'
        run(src1)
        src2 = f'@var[f; @plist.fmt["{path}"]]'
        g = run(src2)
        assert g["f"] == "binary"
