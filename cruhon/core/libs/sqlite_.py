"""
cruhon/core/libs/sqlite_.py
===========================
SQLite3 wrappers for Cruhon — @sqlite.*

━━━ CONNECTION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sqlite.connect[path]              → sqlite3.Connection
  @sqlite.close[conn]                — close the connection
  @sqlite.commit[conn]               — commit current transaction
  @sqlite.as_dict[conn]              → same conn with row_factory = sqlite3.Row

━━━ QUERY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sqlite.fetchall[conn; sql]        → list of rows
  @sqlite.fetchall[conn; sql; params]→ parameterized fetchall
  @sqlite.fetchone[conn; sql]        → single row or None
  @sqlite.fetchone[conn; sql; params]→ parameterized fetchone
  @sqlite.fetchmany[conn; sql; n]    → first n rows
  @sqlite.execute[conn; sql]         → cursor
  @sqlite.execute[conn; sql; params] → cursor (parameterized)

━━━ ONE-SHOT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sqlite.query[path; sql]           → open, fetchall, close
  @sqlite.query[path; sql; params]   → parameterized
  @sqlite.run[path; sql]             → open, execute, commit, close
  @sqlite.run[path; sql; params]     → parameterized

━━━ WRITE HELPERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sqlite.insert[conn; table; dict]  — INSERT row from a dict
  @sqlite.delete[conn; table; col; val] — DELETE WHERE col = val
  @sqlite.update[conn; table; data_dict; where_col; where_val]

━━━ INTROSPECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sqlite.tables[conn]               → list of table names
  @sqlite.columns[conn; table]       → list of column names
  @sqlite.count[conn; table]         → row count (int)
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

    register_lib_call("sqlite", "as_dict",
        lambda a: (
            f"(lambda _c: (setattr(_c, 'row_factory', __import__('sqlite3').Row), _c)[-1])({a[0]})"
        ))

    # ── Query ─────────────────────────────────────────────────
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
            f"(lambda _c, _s, _n: _c.execute(_s).fetchmany(_n))({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _c, _s: _c.execute(_s).fetchmany())({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "execute",
        lambda a: (
            f"(lambda _c, _s, _p: _c.execute(_s, _p))({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _c, _s: _c.execute(_s))({a[0]}, {a[1]})"
        ))

    # ── One-shot ──────────────────────────────────────────────
    register_lib_call("sqlite", "query",
        lambda a: (
            f"(lambda _p, _s, _ps: (lambda _c: (_c.execute(_s, _ps).fetchall(), _c.close())[0])(__import__('sqlite3').connect(_p)))({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _p, _s: (lambda _c: (_c.execute(_s).fetchall(), _c.close())[0])(__import__('sqlite3').connect(_p)))({a[0]}, {a[1]})"
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

    register_lib_call("sqlite", "delete",
        lambda a: (
            f"(lambda _c, _t, _col, _val: _c.execute("
            f"'DELETE FROM ' + _t + ' WHERE ' + _col + ' = ?', [_val]))({a[0]}, {a[1]}, {a[2]}, {a[3]})"
        ))

    register_lib_call("sqlite", "update",
        lambda a: (
            f"(lambda _c, _t, _d, _wc, _wv: _c.execute("
            f"'UPDATE ' + _t + ' SET ' + ', '.join(_k + ' = ?' for _k in _d) + ' WHERE ' + _wc + ' = ?', "
            f"list(_d.values()) + [_wv]))({a[0]}, {a[1]}, {a[2]}, {a[3]}, {a[4]})"
        ))

    # ── Introspect ────────────────────────────────────────────
    register_lib_call("sqlite", "tables",
        lambda a: (
            f"[_r[0] for _r in {a[0]}.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name\").fetchall()]"
        ))

    register_lib_call("sqlite", "columns",
        lambda a: (
            f"(lambda _c, _t: [_d[1] for _d in _c.execute('PRAGMA table_info(' + _t + ')').fetchall()])({a[0]}, {a[1]})"
        ))

    register_lib_call("sqlite", "count",
        lambda a: (
            f"(lambda _c, _t: _c.execute('SELECT COUNT(*) FROM ' + _t).fetchone()[0])({a[0]}, {a[1]})"
        ))
