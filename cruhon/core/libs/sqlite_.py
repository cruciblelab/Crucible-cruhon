"""
cruhon/core/libs/sqlite_.py
===========================
SQLite3 wrappers for Cruhon — @sqlite.*

━━━ CONNECTION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sqlite.connect[path]                   → Connection  (":memory:" for RAM)
  @sqlite.connect[path; check_same_thread=False]
  @sqlite.close[conn]
  @sqlite.commit[conn]
  @sqlite.rollback[conn]
  @sqlite.begin[conn]                     — begin explicit transaction
  @sqlite.in_transaction[conn]            → bool
  @sqlite.set_timeout[conn; ms]           — busy timeout (ms)
  @sqlite.as_dict[conn]                   → conn with row_factory = sqlite3.Row

━━━ QUERY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sqlite.execute[conn; sql]              → cursor
  @sqlite.execute[conn; sql; params]
  @sqlite.executemany[conn; sql; rows]    — batch parameterized execute
  @sqlite.executescript[conn; sql]        — multi-statement SQL (no params)
  @sqlite.fetchall[conn; sql]             → list of rows
  @sqlite.fetchall[conn; sql; params]
  @sqlite.fetchone[conn; sql]             → row or None
  @sqlite.fetchone[conn; sql; params]
  @sqlite.fetchmany[conn; sql; n]         → first n rows
  @sqlite.fetchmany[conn; sql; n; params]
  @sqlite.scalar[conn; sql]              → single value (first col of first row)
  @sqlite.scalar[conn; sql; params]

━━━ ONE-SHOT (open → query/run → close) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sqlite.query[path; sql]               → list of rows
  @sqlite.query[path; sql; params]
  @sqlite.query_one[path; sql]           → single row or None
  @sqlite.query_one[path; sql; params]
  @sqlite.run[path; sql]                 — execute + commit + close
  @sqlite.run[path; sql; params]

━━━ WRITE HELPERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sqlite.insert[conn; table; dict]       — INSERT one row from dict
  @sqlite.insert_many[conn; table; rows]  — INSERT many rows (list of dicts)
  @sqlite.upsert[conn; table; dict; conflict_col]  — INSERT OR REPLACE
  @sqlite.update[conn; table; data; where_col; where_val]
  @sqlite.delete[conn; table; col; val]
  @sqlite.truncate[conn; table]           — DELETE all rows

━━━ TABLE MANAGEMENT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sqlite.create_table[conn; table; schema]  — schema = {"col": "TYPE", ...}
  @sqlite.create_table[conn; table; schema; if_not_exists=True]
  @sqlite.drop_table[conn; table]
  @sqlite.drop_table[conn; table; if_exists=True]
  @sqlite.table_exists[conn; table]       → bool
  @sqlite.tables[conn]                    → list of table names
  @sqlite.columns[conn; table]            → list of column names
  @sqlite.column_types[conn; table]       → dict {col: type}
  @sqlite.count[conn; table]              → row count
  @sqlite.index_create[conn; table; col]  — CREATE INDEX
  @sqlite.index_drop[conn; index_name]    — DROP INDEX

━━━ RESULT HELPERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sqlite.as_dicts[rows]                  → list of plain dicts
  @sqlite.row_as_dict[row]               → single sqlite3.Row → dict
  @sqlite.last_id[conn]                   → last insert rowid
  @sqlite.changes[conn]                   → rows changed by last statement

━━━ MAINTENANCE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sqlite.vacuum[conn]
  @sqlite.backup[conn; dest_path]
  @sqlite.integrity_check[conn]           → "ok" or error string
  @sqlite.pragma[conn; key]              → pragma value
  @sqlite.pragma[conn; key; value]       — set pragma
"""
from ..registry import register_lib, register_lib_call


def register():
    register_lib("sqlite", None)

    # ── Connection ────────────────────────────────────────────
    register_lib_call("sqlite", "connect",
        lambda a: f"__import__('sqlite3').connect({a[0]})")

    register_lib_call("sqlite", "close",
        lambda a: f"(lambda _c: _c.close())({a[0]})")

    register_lib_call("sqlite", "commit",
        lambda a: f"(lambda _c: _c.commit())({a[0]})")

    register_lib_call("sqlite", "rollback",
        lambda a: f"(lambda _c: _c.rollback())({a[0]})")

    register_lib_call("sqlite", "begin",
        lambda a: f"(lambda _c: _c.execute('BEGIN'))({a[0]})")

    register_lib_call("sqlite", "in_transaction",
        lambda a: f"{a[0]}.in_transaction")

    register_lib_call("sqlite", "set_timeout",
        lambda a: f"(lambda _c, _t: (setattr(_c, 'timeout', int(_t)), _c)[-1])({a[0]}, {a[1]})")

    register_lib_call("sqlite", "as_dict",
        lambda a: (
            f"(lambda _c: (setattr(_c, 'row_factory', __import__('sqlite3').Row), _c)[-1])({a[0]})"
        ))

    # ── Execute ───────────────────────────────────────────────
    register_lib_call("sqlite", "execute",
        lambda a: (
            f"(lambda _c, _s, _p: _c.execute(_s, _p))({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _c, _s: _c.execute(_s))({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "executemany",
        lambda a: (
            f"(lambda _c, _s, _rows: _c.executemany(_s, _rows))({a[0]}, {a[1]}, {a[2]})"
        ))

    register_lib_call("sqlite", "executescript",
        lambda a: f"(lambda _c, _s: _c.executescript(_s))({a[0]}, {a[1]})")

    # ── Fetch ─────────────────────────────────────────────────
    register_lib_call("sqlite", "fetchall",
        lambda a: (
            f"(lambda _c, _s, _p: _c.execute(_s, _p).fetchall())({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _c, _s: _c.execute(_s).fetchall())({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "fetchone",
        lambda a: (
            f"(lambda _c, _s, _p: _c.execute(_s, _p).fetchone())({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _c, _s: _c.execute(_s).fetchone())({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "fetchmany",
        lambda a: (
            f"(lambda _c, _s, _n, _p: _c.execute(_s, _p).fetchmany(int(_n)))({a[0]}, {a[1]}, {a[2]}, {a[3]})"
            if len(a) > 3 else
            f"(lambda _c, _s, _n: _c.execute(_s).fetchmany(int(_n)))({a[0]}, {a[1]}, {a[2]})"
        ))

    register_lib_call("sqlite", "scalar",
        lambda a: (
            f"(lambda _c, _s, _p: (_c.execute(_s, _p).fetchone() or [None])[0])({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _c, _s: (_c.execute(_s).fetchone() or [None])[0])({a[0]}, {a[1]})"
        ))

    # ── One-shot ──────────────────────────────────────────────
    register_lib_call("sqlite", "query",
        lambda a: (
            f"(lambda _p, _s, _ps: (lambda _c: (_c.execute(_s, _ps).fetchall(), _c.close())[0])(__import__('sqlite3').connect(_p)))({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _p, _s: (lambda _c: (_c.execute(_s).fetchall(), _c.close())[0])(__import__('sqlite3').connect(_p)))({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "query_one",
        lambda a: (
            f"(lambda _p, _s, _ps: (lambda _c: (_c.execute(_s, _ps).fetchone(), _c.close())[0])(__import__('sqlite3').connect(_p)))({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _p, _s: (lambda _c: (_c.execute(_s).fetchone(), _c.close())[0])(__import__('sqlite3').connect(_p)))({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "run",
        lambda a: (
            f"(lambda _p, _s, _ps: (lambda _c: (_c.execute(_s, _ps), _c.commit(), _c.close()))(__import__('sqlite3').connect(_p)))({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _p, _s: (lambda _c: (_c.execute(_s), _c.commit(), _c.close()))(__import__('sqlite3').connect(_p)))({a[0]}, {a[1]})"
        ))

    # ── Write helpers ─────────────────────────────────────────
    register_lib_call("sqlite", "insert",
        lambda a: (
            f"(lambda _c, _t, _d: _c.execute("
            f"'INSERT INTO ' + _t + ' (' + ', '.join(_d.keys()) + ') VALUES (' + ', '.join(['?'] * len(_d)) + ')', "
            f"list(_d.values())))({a[0]}, {a[1]}, {a[2]})"
        ))

    register_lib_call("sqlite", "insert_many",
        lambda a: (
            f"(lambda _c, _t, _rows: _c.executemany("
            f"'INSERT INTO ' + _t + ' (' + ', '.join(_rows[0].keys()) + ') VALUES (' + ', '.join(['?'] * len(_rows[0])) + ')', "
            f"[list(_r.values()) for _r in _rows]) if _rows else None)({a[0]}, {a[1]}, {a[2]})"
        ))

    register_lib_call("sqlite", "upsert",
        lambda a: (
            f"(lambda _c, _t, _d, _cc: _c.execute("
            f"'INSERT OR REPLACE INTO ' + _t + ' (' + ', '.join(_d.keys()) + ') VALUES (' + ', '.join(['?'] * len(_d)) + ')', "
            f"list(_d.values())))({a[0]}, {a[1]}, {a[2]}, {a[3]})"
        ))

    register_lib_call("sqlite", "update",
        lambda a: (
            f"(lambda _c, _t, _d, _wc, _wv: _c.execute("
            f"'UPDATE ' + _t + ' SET ' + ', '.join(_k + ' = ?' for _k in _d) + ' WHERE ' + _wc + ' = ?', "
            f"list(_d.values()) + [_wv]))({a[0]}, {a[1]}, {a[2]}, {a[3]}, {a[4]})"
        ))

    register_lib_call("sqlite", "delete",
        lambda a: (
            f"(lambda _c, _t, _col, _val: _c.execute("
            f"'DELETE FROM ' + _t + ' WHERE ' + _col + ' = ?', [_val]))({a[0]}, {a[1]}, {a[2]}, {a[3]})"
        ))

    register_lib_call("sqlite", "truncate",
        lambda a: f"(lambda _c, _t: _c.execute('DELETE FROM ' + _t))({a[0]}, {a[1]})")

    # ── Table management ──────────────────────────────────────
    register_lib_call("sqlite", "create_table",
        lambda a: (
            f"(lambda _c, _t, _s: _c.execute("
            f"'CREATE TABLE IF NOT EXISTS ' + _t + ' (' + ', '.join(_k + ' ' + _v for _k, _v in _s.items()) + ')'))({a[0]}, {a[1]}, {a[2]})"
        ))

    register_lib_call("sqlite", "drop_table",
        lambda a: (
            f"(lambda _c, _t: _c.execute('DROP TABLE IF EXISTS ' + _t))({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "table_exists",
        lambda a: (
            f"(lambda _c, _t: bool(_c.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name=?\", [_t]).fetchone()))({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "tables",
        lambda a: (
            f"[_r[0] for _r in {a[0]}.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name\").fetchall()]"
        ))

    register_lib_call("sqlite", "columns",
        lambda a: (
            f"(lambda _c, _t: [_d[1] for _d in _c.execute('PRAGMA table_info(' + _t + ')').fetchall()])({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "column_types",
        lambda a: (
            f"(lambda _c, _t: {{_d[1]: _d[2] for _d in _c.execute('PRAGMA table_info(' + _t + ')').fetchall()}})({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "count",
        lambda a: (
            f"(lambda _c, _t: _c.execute('SELECT COUNT(*) FROM ' + _t).fetchone()[0])({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "index_create",
        lambda a: (
            f"(lambda _c, _t, _col: _c.execute("
            f"'CREATE INDEX IF NOT EXISTS idx_' + _t + '_' + _col + ' ON ' + _t + '(' + _col + ')'))({a[0]}, {a[1]}, {a[2]})"
        ))

    register_lib_call("sqlite", "index_drop",
        lambda a: f"(lambda _c, _n: _c.execute('DROP INDEX IF EXISTS ' + _n))({a[0]}, {a[1]})")

    # ── Result helpers ────────────────────────────────────────
    register_lib_call("sqlite", "as_dicts",
        lambda a: f"[dict(_r) for _r in {a[0]}]")

    register_lib_call("sqlite", "row_as_dict",
        lambda a: f"dict({a[0]})")

    register_lib_call("sqlite", "last_id",
        lambda a: f"{a[0]}.execute('SELECT last_insert_rowid()').fetchone()[0]")

    register_lib_call("sqlite", "changes",
        lambda a: f"{a[0]}.execute('SELECT changes()').fetchone()[0]")

    # ── Maintenance ───────────────────────────────────────────
    register_lib_call("sqlite", "vacuum",
        lambda a: f"(lambda _c: _c.execute('VACUUM'))({a[0]})")

    register_lib_call("sqlite", "backup",
        lambda a: (
            f"(lambda _c, _dst: (lambda _d: (_c.backup(_d), _d.close()))(__import__('sqlite3').connect(_dst)))({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "integrity_check",
        lambda a: (
            f"(lambda _c: _c.execute('PRAGMA integrity_check').fetchone()[0])({a[0]})"
        ))

    register_lib_call("sqlite", "pragma",
        lambda a: (
            f"(lambda _c, _k, _v: _c.execute('PRAGMA ' + _k + ' = ' + str(_v)))({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _c, _k: _c.execute('PRAGMA ' + _k).fetchone()[0])({a[0]}, {a[1]})"
        ))
