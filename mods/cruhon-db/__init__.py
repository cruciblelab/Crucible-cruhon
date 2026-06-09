"""
cruhon-db — full-coverage database plugin for Cruhon  (138 commands)

Sync backends:  SQLite (built-in)  ·  PostgreSQL (psycopg2)  ·  MySQL (pymysql)
Async backends: SQLite (aiosqlite) ·  PostgreSQL (asyncpg)   ·  MySQL (aiomysql)

━━━ CONNECTION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @db.connect["sqlite:///data.db"]      — also :memory: / postgres:// / mysql://
  @db.close[]
  @db.ping[]              → bool
  @db.reconnect[]
  @db.in_transaction[]    → bool

━━━ CONNECTION INFO & RAW ACCESS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @db.connection[]        → raw connection object  (full Python freedom)
  @db.cursor_obj[]        → raw cursor object
  @db.db_type[]           → "sqlite" | "postgres" | "mysql"
  @db.dsn[]               → DSN string used to connect
  @db.closed[]            → bool
  @db.conn_info[]         → dict: host/port/user/db/type
  @db.server_version[]    → version string (all backends)
  @db.autocommit[]        → current autocommit bool
  @db.autocommit[bool]    — set autocommit
  @db.isolation_level[]   → current isolation level
  @db.isolation_level[lv] — set isolation level
  @db.total_changes[]     → total rows changed since open (sqlite)

━━━ CORE EXEC / QUERY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @db.exec[sql; params...]         — INSERT/UPDATE/DELETE/DDL → lastrowid
  @db.execmany[sql; rows_list]     — bulk parameterized SQL
  @db.query[sql; params...]        — SELECT → list of dicts (stored)
  @db.fetchone[]                   → next row from open cursor
  @db.fetchmany[n]                 → next n rows from open cursor
  @db.fetchall[]                   → all remaining rows from open cursor

━━━ CRUD SHORTCUTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @db.insert[table; {col: val}]
  @db.insertmany[table; [{...}, ...]]
  @db.update[table; {col: val}; where; params...]   → rowcount
  @db.delete[table; where; params...]               → rowcount
  @db.get[table; where; params...]                  → first row or None
  @db.getall[table]  /  @db.getall[table; where; params...]
  @db.truncate[table]

━━━ CURSOR CONTROL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @db.scroll[n]                    — relative scroll (pg/mysql)
  @db.scroll[n; "absolute"]        — absolute scroll
  @db.rownumber[]                  → current row index (pg/mysql)
  @db.arraysize[]                  → cursor.arraysize
  @db.arraysize[n]                 — set cursor.arraysize
  @db.callproc[name; args]         — call stored procedure (pg/mysql)
  @db.nextset[]                    — move to next result set (mysql)
  @db.cursor_close[]               — close current cursor

━━━ SCHEMA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @db.create[sql]
  @db.drop[table]
  @db.exists[table]      → bool
  @db.tables[]           → list
  @db.views[]            → list
  @db.schema[table]      → list of {name, type, nullable, default, pk}
  @db.indexes[table]     → list of index dicts
  @db.rename[old; new]
  @db.index_create[table; col]
  @db.index_drop[name]

━━━ RESULT ACCESS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @db.rows[]  /  @db.rows[result]
  @db.one[]   /  @db.one[result]
  @db.row[n]
  @db.col[name]
  @db.cols[]
  @db.count[] /  @db.count[result]
  @db.rowcount[]
  @db.lastid[]

━━━ TRANSACTIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @db.begin[]  @db.commit[]  @db.rollback[]
  @db.savepoint[name]  @db.release[name]  @db.rollback_to[name]

━━━ SQLITE-SPECIFIC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @db.pragma[name]  /  @db.pragma[name; value]
  @db.vacuum[]
  @db.backup[path]
  @db.restore[path]
  @db.script[sql]             — executescript (multi-statement)
  @db.func[name; nargs; fn]   — create_function (Python → SQL)
  @db.aggregate[name; nargs; cls]  — create_aggregate
  @db.collation[name; fn]     — create_collation
  @db.dump[]                  → list of SQL strings (iterdump)
  @db.serialize[]             → bytes (py 3.11+)
  @db.deserialize[data]       — load from bytes (py 3.11+)
  @db.text_factory[fn]        — set text decoding callable
  @db.trace[fn]               — set_trace_callback
  @db.progress[n; fn]         — set_progress_handler
  @db.authorizer[fn]          — set_authorizer
  @db.enable_ext[bool]        — enable_load_extension
  @db.load_ext[path]          — load_extension
  @db.row_factory[fn]         — set row_factory callable
  @db.total_changes[]         → int

━━━ POSTGRESQL-SPECIFIC (psycopg2) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @db.pg_copy_from[path; table]           — COPY file → table
  @db.pg_copy_to[path; table]             — COPY table → file
  @db.pg_copy_expert[sql; path]           — COPY with custom SQL
  @db.pg_mogrify[sql; params]             → formatted SQL string
  @db.pg_listen[channel]                  — LISTEN channel
  @db.pg_unlisten[channel]                — UNLISTEN channel
  @db.pg_notify[channel; payload]         — NOTIFY
  @db.pg_poll[]                           — poll async notifications
  @db.pg_notifications[]                  → list of pending NOTIFYs
  @db.pg_notices[]                        → list of server notices
  @db.pg_cancel[]                         — cancel current operation
  @db.pg_reset[]                          — reset connection
  @db.pg_pid[]                            → backend PID
  @db.pg_param[name]                      → server parameter value
  @db.pg_isolation[level]                 — set isolation level
  @db.pg_encoding[enc]                    — set client encoding
  @db.pg_autocommit[bool]                 — set autocommit
  @db.pg_status[]                         → transaction status int
  @db.pg_server_version[]                 → int (e.g. 140001)
  @db.pg_tpc_begin[xid]
  @db.pg_tpc_prepare[]
  @db.pg_tpc_commit[]
  @db.pg_tpc_rollback[]
  @db.pg_tpc_recover[]                    → list of pending XIDs

━━━ MYSQL-SPECIFIC (pymysql) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @db.my_select_db[name]    — USE database
  @db.my_server_info[]      → version string
  @db.my_thread_id[]        → int
  @db.my_charset[name]      — set charset (no arg = get current)
  @db.my_kill[tid]          — kill thread
  @db.my_warnings[]         → list of warning dicts
  @db.my_nextset[]          — move to next result set

━━━ ASYNC (use inside @async[main]...@end) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @db.async_connect[dsn]  @db.async_close[]
  @db.async_query[sql; params...]       → list of dicts
  @db.async_exec[sql; params...]        → lastrowid
  @db.async_execmany[sql; rows]         — bulk SQL
  @db.async_insert[table; data]         → lastrowid
  @db.async_insertmany[table; rows]
  @db.async_get[table; where; params...]  → first row or None
  @db.async_getall[table]  /  @db.async_getall[table; where; params...]
  @db.async_begin[]  @db.async_commit[]  @db.async_rollback[]
  @db.async_one[]  @db.async_rows[]  @db.async_count[]
  @db.async_rowcount[]  @db.async_cols[]

  — Streaming cursor:
  @db.async_cursor_open[sql; params...]  — open streaming cursor
  @db.async_fetchone[]                   → next row dict or None
  @db.async_fetchmany[n]                 → next n row dicts
  @db.async_cursor_close[]

  — aiosqlite extras:
  @db.async_script[sql]                  — executescript
  @db.async_func[name; nargs; fn]        — create_function
  @db.async_total_changes[]              → int
  @db.async_dump[]                       → list of SQL strings
  @db.async_in_transaction[]             → bool

  — asyncpg extras:
  @db.async_fetchrow[sql; params...]     → single dict or None
  @db.async_fetchval[sql; col; params...]  → scalar value
  @db.async_copy_from[table; records]    — copy records to table
  @db.async_copy_to[table; path]         — copy table to file
  @db.async_server_version[]             → version namedtuple
  @db.async_pid[]                        → backend PID
  @db.async_is_closed[]                  → bool
  @db.async_terminate[]                  — force close
  @db.async_reset[]                      — reset connection

  — aiomysql extras:
  @db.async_select_db[name]
  @db.async_charset[name]
  @db.async_ping[]
  @db.async_callproc[name; args]
  @db.async_scroll[n]
"""

from __future__ import annotations
import re
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────
# DSN PARSER
# ─────────────────────────────────────────────────────────────

def _parse_dsn(url: str):
    url = url.strip()
    if url.startswith("sqlite:"):
        path = re.sub(r"^sqlite:///", "", url)
        return "sqlite", {"database": path or ":memory:"}
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            rest = url[len(prefix):]
            m = re.match(
                r"(?:([^:@]+)(?::([^@]*))?@)?([^:/]+)(?::(\d+))?(?:/(.*))?$", rest
            )
            if not m:
                raise ValueError(f"[cruhon-db] Cannot parse PostgreSQL DSN: {url!r}")
            user, password, host, port, dbname = m.groups()
            kw: dict = {"host": host or "localhost", "database": dbname or ""}
            if user:     kw["user"] = user
            if password: kw["password"] = password
            if port:     kw["port"] = int(port)
            return "postgres", kw
    if url.startswith("mysql://"):
        rest = url[8:]
        m = re.match(
            r"(?:([^:@]+)(?::([^@]*))?@)?([^:/]+)(?::(\d+))?(?:/(.*))?$", rest
        )
        if not m:
            raise ValueError(f"[cruhon-db] Cannot parse MySQL DSN: {url!r}")
        user, password, host, port, dbname = m.groups()
        kw = {"host": host or "localhost", "db": dbname or ""}
        if user:     kw["user"] = user
        if password: kw["passwd"] = password
        if port:     kw["port"] = int(port)
        return "mysql", kw
    return "sqlite", {"database": url}


# ─────────────────────────────────────────────────────────────
# MAIN DB CLASS
# ─────────────────────────────────────────────────────────────

class _DB:
    def __init__(self):
        # Sync state
        self._conn = None
        self._cursor = None
        self._db_type: Optional[str] = None
        self._dsn: Optional[str] = None
        self._last_result: list = []
        self._last_id: Optional[Any] = None
        self._last_rowcount: int = 0
        self._last_cols: list = []
        self._in_transaction: bool = False
        # Async state
        self._async_conn = None
        self._async_cursor = None           # streaming cursor
        self._async_db_type: Optional[str] = None
        self._async_last_result: list = []
        self._async_last_id: Optional[Any] = None
        self._async_last_rowcount: int = 0
        self._async_last_cols: list = []

    # ── Internal helpers ───────────────────────────────────────

    def _require_conn(self):
        if self._conn is None:
            raise RuntimeError("[cruhon-db] No active connection. Call @db.connect first.")

    def _require_sqlite(self, cmd: str):
        self._require_conn()
        if self._db_type != "sqlite":
            raise RuntimeError(f"[cruhon-db] @db.{cmd} is SQLite-only.")

    def _require_postgres(self, cmd: str):
        self._require_conn()
        if self._db_type != "postgres":
            raise RuntimeError(f"[cruhon-db] @db.{cmd} is PostgreSQL-only.")

    def _require_mysql(self, cmd: str):
        self._require_conn()
        if self._db_type != "mysql":
            raise RuntimeError(f"[cruhon-db] @db.{cmd} is MySQL-only.")

    def _auto_commit(self):
        if not self._in_transaction and self._db_type in ("postgres", "mysql"):
            self._conn.commit()

    def _row_to_dict(self, row) -> Optional[dict]:
        if row is None:
            return None
        if isinstance(row, dict):
            return dict(row)
        if hasattr(row, "keys"):
            return dict(row)
        if self._cursor and self._cursor.description:
            cols = [d[0] for d in self._cursor.description]
            return dict(zip(cols, row))
        return {"_": row}

    def _store_result(self, rows):
        self._last_result = [self._row_to_dict(r) for r in rows]
        if self._cursor and self._cursor.description:
            self._last_cols = [d[0] for d in self._cursor.description]
        elif self._last_result:
            self._last_cols = list(self._last_result[0].keys())
        else:
            self._last_cols = []
        return self._last_result

    # ── CONNECTION ────────────────────────────────────────────

    def connect(self, args: list):
        if not args:
            raise RuntimeError("[cruhon-db] @db.connect requires a DSN.")
        if self._conn is not None:
            self.close([])
        dsn = str(args[0])
        self._dsn = dsn
        db_type, kwargs = _parse_dsn(dsn)
        self._db_type = db_type
        if db_type == "sqlite":
            import sqlite3
            self._conn = sqlite3.connect(kwargs["database"], isolation_level=None)
            self._conn.row_factory = sqlite3.Row
            self._cursor = self._conn.cursor()
        elif db_type == "postgres":
            try:
                import psycopg2, psycopg2.extras
                self._conn = psycopg2.connect(**kwargs)
                self._cursor = self._conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                )
            except ImportError:
                raise RuntimeError(
                    "[cruhon-db] PostgreSQL requires psycopg2. pip install psycopg2-binary"
                )
        elif db_type == "mysql":
            try:
                import pymysql, pymysql.cursors
                kwargs["cursorclass"] = pymysql.cursors.DictCursor
                self._conn = pymysql.connect(**kwargs)
                self._cursor = self._conn.cursor()
            except ImportError:
                raise RuntimeError(
                    "[cruhon-db] MySQL requires pymysql. pip install pymysql"
                )
        return self._conn

    def close(self, args: list):
        if self._conn is not None:
            try: self._conn.close()
            except Exception: pass
        self._conn = None
        self._cursor = None
        self._db_type = None
        self._in_transaction = False

    def ping(self, args: list):
        if self._conn is None:
            return False
        try:
            if self._db_type == "sqlite":
                self._cursor.execute("SELECT 1")
            elif self._db_type == "postgres":
                self._cursor.execute("SELECT 1")
            elif self._db_type == "mysql":
                self._conn.ping(reconnect=False)
            return True
        except Exception:
            return False

    def reconnect(self, args: list):
        if not self._dsn:
            raise RuntimeError("[cruhon-db] No previous DSN for reconnect.")
        self.connect([self._dsn])

    def in_transaction(self, args: list):
        return self._in_transaction

    # ── CONNECTION INFO & RAW ACCESS ──────────────────────────

    def connection(self, args: list):
        """Return the raw connection object — full Python freedom."""
        return self._conn

    def cursor_obj(self, args: list):
        """Return the raw cursor object."""
        return self._cursor

    def db_type(self, args: list):
        """Return 'sqlite', 'postgres', or 'mysql'."""
        return self._db_type

    def dsn(self, args: list):
        """Return the DSN string used to connect."""
        return self._dsn

    def closed(self, args: list):
        """Return True if no active connection."""
        return self._conn is None

    def conn_info(self, args: list):
        """Return dict with host/port/user/db/type metadata."""
        if self._conn is None:
            return {"type": None, "connected": False}
        info: dict = {"type": self._db_type, "connected": True}
        if self._db_type == "sqlite":
            info["database"] = self._dsn or ":memory:"
        elif self._db_type == "postgres":
            try:
                params = self._conn.get_dsn_parameters()
                info.update(params)
            except Exception:
                pass
        elif self._db_type == "mysql":
            info["host"] = getattr(self._conn, "host", None)
            info["port"] = getattr(self._conn, "port", None)
            info["user"] = getattr(self._conn, "user", None)
            info["db"]   = getattr(self._conn, "db", None)
        return info

    def server_version(self, args: list):
        """Return the server version string for the current backend."""
        self._require_conn()
        if self._db_type == "sqlite":
            import sqlite3
            return sqlite3.sqlite_version
        elif self._db_type == "postgres":
            v = self._conn.server_version
            major = v // 10000
            minor = (v % 10000) // 100
            patch = v % 100
            return f"{major}.{minor}.{patch}"
        elif self._db_type == "mysql":
            return self._conn.get_server_info()

    def autocommit(self, args: list):
        """
        @db.autocommit[]       → current autocommit bool
        @db.autocommit[True]   — enable autocommit
        @db.autocommit[False]  — disable autocommit
        """
        self._require_conn()
        if not args:
            if self._db_type == "sqlite":
                return self._conn.isolation_level is None
            elif self._db_type == "postgres":
                return self._conn.autocommit
            elif self._db_type == "mysql":
                return bool(getattr(self._conn, "_autocommit", False))
        value = bool(args[0])
        if self._db_type == "sqlite":
            self._conn.isolation_level = None if value else ""
        elif self._db_type == "postgres":
            self._conn.autocommit = value
        elif self._db_type == "mysql":
            self._conn.autocommit(value)
        return value

    def isolation_level(self, args: list):
        """
        @db.isolation_level[]       → current isolation level
        @db.isolation_level[level]  — set isolation level
        """
        self._require_conn()
        if not args:
            if self._db_type == "sqlite":
                return self._conn.isolation_level
            elif self._db_type == "postgres":
                return self._conn.isolation_level
            elif self._db_type == "mysql":
                self._cursor.execute(
                    "SELECT @@SESSION.transaction_isolation"
                )
                row = self._cursor.fetchone()
                return list(row.values())[0] if row else None
        level = str(args[0])
        if self._db_type == "sqlite":
            self._conn.isolation_level = level
        elif self._db_type == "postgres":
            import psycopg2.extensions as ext
            levels = {
                "SERIALIZABLE":    ext.ISOLATION_LEVEL_SERIALIZABLE,
                "REPEATABLE READ": ext.ISOLATION_LEVEL_REPEATABLE_READ,
                "READ COMMITTED":  ext.ISOLATION_LEVEL_READ_COMMITTED,
                "READ UNCOMMITTED":ext.ISOLATION_LEVEL_READ_UNCOMMITTED,
                "AUTOCOMMIT":      ext.ISOLATION_LEVEL_AUTOCOMMIT,
            }
            self._conn.set_isolation_level(levels.get(level.upper(), int(level)))
        elif self._db_type == "mysql":
            self._cursor.execute(
                f"SET SESSION TRANSACTION ISOLATION LEVEL {level}"
            )
        return level

    def total_changes(self, args: list):
        """Return total rows modified since the connection was opened (sqlite)."""
        self._require_sqlite("total_changes")
        return self._conn.total_changes

    # ── CURSOR CONTROL ────────────────────────────────────────

    def scroll(self, args: list):
        """
        @db.scroll[n]              — relative scroll by n rows
        @db.scroll[n; "absolute"]  — scroll to absolute position n
        """
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.scroll requires a value.")
        n = int(args[0])
        mode = str(args[1]).strip('"\'') if len(args) > 1 else "relative"
        if self._db_type == "sqlite":
            raise RuntimeError(
                "[cruhon-db] @db.scroll: SQLite cursors are forward-only."
            )
        self._cursor.scroll(n, mode=mode)

    def rownumber(self, args: list):
        """Return current cursor row index (psycopg2/pymysql)."""
        self._require_conn()
        return getattr(self._cursor, "rownumber", None)

    def arraysize(self, args: list):
        """
        @db.arraysize[]    → current cursor.arraysize
        @db.arraysize[n]   — set cursor.arraysize
        """
        self._require_conn()
        if not args:
            return self._cursor.arraysize
        self._cursor.arraysize = int(args[0])
        return self._cursor.arraysize

    def callproc(self, args: list):
        """
        @db.callproc[name; args_list]
        Call a stored procedure. Returns result rows stored in last-result.
        """
        self._require_conn()
        if self._db_type == "sqlite":
            raise RuntimeError(
                "[cruhon-db] @db.callproc: SQLite does not support stored procedures."
            )
        if not args:
            raise RuntimeError("[cruhon-db] @db.callproc requires a procedure name.")
        name = str(args[0])
        proc_args = args[1] if len(args) > 1 else []
        self._cursor.callproc(name, proc_args)
        try:
            return self._store_result(self._cursor.fetchall())
        except Exception:
            return []

    def nextset(self, args: list):
        """Advance to the next result set (MySQL multiple statements)."""
        self._require_conn()
        if not hasattr(self._cursor, "nextset"):
            raise RuntimeError(
                "[cruhon-db] @db.nextset is not supported by this backend."
            )
        result = self._cursor.nextset()
        if result:
            return self._store_result(self._cursor.fetchall())
        return None

    def cursor_close(self, args: list):
        """Close the current cursor."""
        if self._cursor is not None:
            try: self._cursor.close()
            except Exception: pass
            if self._conn is not None:
                if self._db_type == "sqlite":
                    import sqlite3
                    self._cursor = self._conn.cursor()
                elif self._db_type == "postgres":
                    import psycopg2.extras
                    self._cursor = self._conn.cursor(
                        cursor_factory=psycopg2.extras.RealDictCursor
                    )
                elif self._db_type == "mysql":
                    self._cursor = self._conn.cursor()

    # ── CORE EXEC / QUERY ─────────────────────────────────────

    def exec(self, args: list):
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.exec requires SQL.")
        sql = str(args[0])
        params = tuple(args[1:]) if len(args) > 1 else ()
        self._cursor.execute(sql, params)
        self._last_id = self._cursor.lastrowid
        self._last_rowcount = max(self._cursor.rowcount or 0, 0)
        self._auto_commit()
        return self._last_id

    def execmany(self, args: list):
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.execmany requires sql and rows_list.")
        sql = str(args[0])
        rows = args[1]
        self._cursor.executemany(sql, rows)
        self._last_rowcount = max(self._cursor.rowcount or 0, 0)
        self._auto_commit()

    def query(self, args: list):
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.query requires SQL.")
        sql = str(args[0])
        params = tuple(args[1:]) if len(args) > 1 else ()
        self._cursor.execute(sql, params)
        return self._store_result(self._cursor.fetchall())

    def fetchone(self, args: list):
        self._require_conn()
        return self._row_to_dict(self._cursor.fetchone())

    def fetchmany(self, args: list):
        self._require_conn()
        n = int(args[0]) if args else 1
        return [self._row_to_dict(r) for r in self._cursor.fetchmany(n)]

    def fetchall(self, args: list):
        self._require_conn()
        return self._store_result(self._cursor.fetchall())

    # ── CRUD SHORTCUTS ────────────────────────────────────────

    def insert(self, args: list):
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.insert requires table and data dict.")
        table, data = str(args[0]), args[1]
        if not isinstance(data, dict) or not data:
            raise RuntimeError("[cruhon-db] @db.insert: data must be a non-empty dict.")
        cols = list(data.keys())
        ph = "?" if self._db_type == "sqlite" else "%s"
        sql = (
            f"INSERT INTO {table} ({', '.join(cols)}) "
            f"VALUES ({', '.join(ph for _ in cols)})"
        )
        self._cursor.execute(sql, list(data.values()))
        self._last_id = self._cursor.lastrowid
        self._last_rowcount = 1
        self._auto_commit()
        return self._last_id

    def insertmany(self, args: list):
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.insertmany requires table and rows_list.")
        table, rows = str(args[0]), args[1]
        if not isinstance(rows, (list, tuple)) or not rows:
            raise RuntimeError("[cruhon-db] @db.insertmany: rows must be a non-empty list.")
        cols = list(rows[0].keys())
        ph = "?" if self._db_type == "sqlite" else "%s"
        sql = (
            f"INSERT INTO {table} ({', '.join(cols)}) "
            f"VALUES ({', '.join(ph for _ in cols)})"
        )
        self._cursor.executemany(sql, [tuple(r[c] for c in cols) for r in rows])
        self._last_rowcount = len(rows)
        self._auto_commit()

    def update(self, args: list):
        self._require_conn()
        if len(args) < 3:
            raise RuntimeError("[cruhon-db] @db.update requires table, data, where.")
        table, data, where = str(args[0]), args[1], str(args[2])
        where_params = list(args[3:])
        ph = "?" if self._db_type == "sqlite" else "%s"
        set_parts = [f"{k} = {ph}" for k in data.keys()]
        sql = f"UPDATE {table} SET {', '.join(set_parts)} WHERE {where}"
        self._cursor.execute(sql, list(data.values()) + where_params)
        self._last_rowcount = max(self._cursor.rowcount or 0, 0)
        self._auto_commit()
        return self._last_rowcount

    def delete(self, args: list):
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.delete requires table and where.")
        table, where = str(args[0]), str(args[1])
        params = list(args[2:])
        self._cursor.execute(f"DELETE FROM {table} WHERE {where}", params)
        self._last_rowcount = max(self._cursor.rowcount or 0, 0)
        self._auto_commit()
        return self._last_rowcount

    def get(self, args: list):
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.get requires table and where.")
        table, where = str(args[0]), str(args[1])
        params = tuple(args[2:])
        self._cursor.execute(f"SELECT * FROM {table} WHERE {where} LIMIT 1", params)
        row = self._cursor.fetchone()
        result = [self._row_to_dict(row)] if row is not None else []
        self._store_result(result)
        return result[0] if result else None

    def getall(self, args: list):
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.getall requires a table name.")
        table = str(args[0])
        if len(args) > 1:
            where, params = str(args[1]), tuple(args[2:])
            self._cursor.execute(f"SELECT * FROM {table} WHERE {where}", params)
        else:
            self._cursor.execute(f"SELECT * FROM {table}")
        return self._store_result(self._cursor.fetchall())

    def truncate(self, args: list):
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.truncate requires a table name.")
        table = str(args[0])
        if self._db_type == "sqlite":
            self._cursor.execute(f"DELETE FROM {table}")
        else:
            self._cursor.execute(f"TRUNCATE TABLE {table}")
        self._auto_commit()

    # ── SCHEMA ────────────────────────────────────────────────

    def create(self, args: list):
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.create requires CREATE TABLE SQL.")
        self._cursor.execute(str(args[0]))
        self._auto_commit()

    def drop(self, args: list):
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.drop requires a table name.")
        self._cursor.execute(f"DROP TABLE IF EXISTS {args[0]}")
        self._auto_commit()

    def exists(self, args: list):
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.exists requires a table name.")
        table = str(args[0])
        if self._db_type == "sqlite":
            self._cursor.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            )
        elif self._db_type == "postgres":
            self._cursor.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name=%s", (table,)
            )
        elif self._db_type == "mysql":
            self._cursor.execute("SHOW TABLES LIKE %s", (table,))
        return self._cursor.fetchone() is not None

    def tables(self, args: list):
        self._require_conn()
        if self._db_type == "sqlite":
            self._cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return [dict(r)["name"] for r in self._cursor.fetchall()]
        elif self._db_type == "postgres":
            self._cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' ORDER BY table_name"
            )
            return [r["table_name"] for r in self._cursor.fetchall()]
        elif self._db_type == "mysql":
            self._cursor.execute("SHOW TABLES")
            return [list(r.values())[0] for r in self._cursor.fetchall()]
        return []

    def views(self, args: list):
        self._require_conn()
        if self._db_type == "sqlite":
            self._cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
            )
            return [dict(r)["name"] for r in self._cursor.fetchall()]
        elif self._db_type == "postgres":
            self._cursor.execute(
                "SELECT table_name FROM information_schema.views "
                "WHERE table_schema='public' ORDER BY table_name"
            )
            return [r["table_name"] for r in self._cursor.fetchall()]
        elif self._db_type == "mysql":
            self._cursor.execute("SHOW FULL TABLES WHERE Table_type='VIEW'")
            return [list(r.values())[0] for r in self._cursor.fetchall()]
        return []

    def schema(self, args: list):
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.schema requires a table name.")
        table = str(args[0])
        if self._db_type == "sqlite":
            self._cursor.execute(f"PRAGMA table_info({table})")
            return [{
                "name":     dict(r)["name"],
                "type":     dict(r)["type"],
                "nullable": not dict(r)["notnull"],
                "default":  dict(r)["dflt_value"],
                "pk":       bool(dict(r)["pk"]),
            } for r in self._cursor.fetchall()]
        elif self._db_type == "postgres":
            self._cursor.execute(
                "SELECT column_name, data_type, is_nullable, column_default, "
                "  (SELECT COUNT(*) FROM information_schema.table_constraints tc "
                "   JOIN information_schema.constraint_column_usage ccu "
                "     USING (constraint_schema, constraint_name) "
                "   WHERE tc.constraint_type='PRIMARY KEY' "
                "     AND tc.table_name=%s AND ccu.column_name=c.column_name) AS is_pk "
                "FROM information_schema.columns c "
                "WHERE table_schema='public' AND table_name=%s "
                "ORDER BY ordinal_position",
                (table, table),
            )
            return [{
                "name":     r["column_name"],
                "type":     r["data_type"],
                "nullable": r["is_nullable"] == "YES",
                "default":  r["column_default"],
                "pk":       r["is_pk"] > 0,
            } for r in self._cursor.fetchall()]
        elif self._db_type == "mysql":
            self._cursor.execute(f"DESCRIBE {table}")
            return [{
                "name":     r["Field"],
                "type":     r["Type"],
                "nullable": r["Null"] == "YES",
                "default":  r["Default"],
                "pk":       r["Key"] == "PRI",
            } for r in self._cursor.fetchall()]
        return []

    def indexes(self, args: list):
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.indexes requires a table name.")
        table = str(args[0])
        if self._db_type == "sqlite":
            self._cursor.execute(f"PRAGMA index_list({table})")
            idx_list = [dict(r) for r in self._cursor.fetchall()]
            result = []
            for idx in idx_list:
                self._cursor.execute(f"PRAGMA index_info({idx['name']})")
                cols = [dict(r)["name"] for r in self._cursor.fetchall()]
                result.append({"name": idx["name"], "unique": bool(idx["unique"]), "columns": cols})
            return result
        elif self._db_type == "postgres":
            self._cursor.execute(
                "SELECT indexname, indexdef FROM pg_indexes WHERE tablename=%s ORDER BY indexname",
                (table,),
            )
            return [{"name": r["indexname"], "def": r["indexdef"]} for r in self._cursor.fetchall()]
        elif self._db_type == "mysql":
            self._cursor.execute(f"SHOW INDEX FROM {table}")
            return self._cursor.fetchall()
        return []

    def rename(self, args: list):
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.rename requires old and new names.")
        old, new = str(args[0]), str(args[1])
        if self._db_type == "mysql":
            self._cursor.execute(f"RENAME TABLE {old} TO {new}")
        else:
            self._cursor.execute(f"ALTER TABLE {old} RENAME TO {new}")
        self._auto_commit()

    def index_create(self, args: list):
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.index_create requires table and col.")
        table, col = str(args[0]), str(args[1])
        idx = f"idx_{table}_{col}"
        if self._db_type == "mysql":
            try: self._cursor.execute(f"CREATE INDEX {idx} ON {table}({col})")
            except Exception: pass
        else:
            self._cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx} ON {table}({col})")
        self._auto_commit()

    def index_drop(self, args: list):
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.index_drop requires an index name.")
        idx = str(args[0])
        if self._db_type == "mysql":
            raise RuntimeError(
                "[cruhon-db] MySQL @db.index_drop: use @db.exec[\"ALTER TABLE t DROP INDEX name\"]"
            )
        self._cursor.execute(f"DROP INDEX IF EXISTS {idx}")
        self._auto_commit()

    # ── RESULT ACCESS ─────────────────────────────────────────

    def rows(self, args: list):
        return args[0] if args else self._last_result

    def one(self, args: list):
        result = args[0] if args else self._last_result
        if isinstance(result, (list, tuple)):
            return result[0] if result else None
        return result

    def row(self, args: list):
        n = int(args[0]) if args else 0
        return self._last_result[n] if 0 <= n < len(self._last_result) else None

    def col(self, args: list):
        if not args: raise RuntimeError("[cruhon-db] @db.col requires a column name.")
        return self._last_result[0].get(str(args[0])) if self._last_result else None

    def cols(self, args: list):
        return list(self._last_cols)

    def count(self, args: list):
        result = args[0] if args else self._last_result
        return len(result) if isinstance(result, (list, tuple)) else 0

    def rowcount(self, args: list):
        return self._last_rowcount

    def lastid(self, args: list):
        return self._last_id

    # ── TRANSACTIONS ──────────────────────────────────────────

    def begin(self, args: list):
        self._require_conn()
        if self._in_transaction:
            return
        self._in_transaction = True
        if self._db_type == "sqlite":
            self._cursor.execute("BEGIN")
        elif self._db_type == "mysql":
            self._cursor.execute("START TRANSACTION")

    def commit(self, args: list):
        self._require_conn()
        self._conn.commit()
        self._in_transaction = False

    def rollback(self, args: list):
        self._require_conn()
        self._conn.rollback()
        self._in_transaction = False

    def savepoint(self, args: list):
        self._require_conn()
        if not args: raise RuntimeError("[cruhon-db] @db.savepoint requires a name.")
        self._cursor.execute(f"SAVEPOINT {args[0]}")

    def release(self, args: list):
        self._require_conn()
        if not args: raise RuntimeError("[cruhon-db] @db.release requires a name.")
        self._cursor.execute(f"RELEASE SAVEPOINT {args[0]}")

    def rollback_to(self, args: list):
        self._require_conn()
        if not args: raise RuntimeError("[cruhon-db] @db.rollback_to requires a name.")
        self._cursor.execute(f"ROLLBACK TO SAVEPOINT {args[0]}")

    # ── SQLITE-SPECIFIC ───────────────────────────────────────

    def pragma(self, args: list):
        self._require_sqlite("pragma")
        if not args: raise RuntimeError("[cruhon-db] @db.pragma requires a name.")
        name = str(args[0])
        if len(args) > 1:
            self._cursor.execute(f"PRAGMA {name} = {args[1]}")
            return args[1]
        self._cursor.execute(f"PRAGMA {name}")
        row = self._cursor.fetchone()
        return dict(row)[name] if row is not None else None

    def vacuum(self, args: list):
        self._require_sqlite("vacuum")
        self._cursor.execute("VACUUM")

    def backup(self, args: list):
        self._require_sqlite("backup")
        if not args: raise RuntimeError("[cruhon-db] @db.backup requires a path.")
        import sqlite3
        dest = sqlite3.connect(str(args[0]))
        self._conn.backup(dest)
        dest.close()

    def restore(self, args: list):
        if not args: raise RuntimeError("[cruhon-db] @db.restore requires a path.")
        self.connect([f"sqlite:///{args[0]}"])

    def script(self, args: list):
        """@db.script[sql]  — execute multiple ; separated SQL statements (sqlite)."""
        self._require_sqlite("script")
        if not args: raise RuntimeError("[cruhon-db] @db.script requires SQL.")
        self._conn.executescript(str(args[0]))

    def func(self, args: list):
        """@db.func[name; nargs; callable]  — register Python fn as SQLite SQL function."""
        self._require_sqlite("func")
        if len(args) < 3:
            raise RuntimeError("[cruhon-db] @db.func requires name, nargs, callable.")
        self._conn.create_function(str(args[0]), int(args[1]), args[2])

    def aggregate(self, args: list):
        """@db.aggregate[name; nargs; class]  — register aggregate function (sqlite)."""
        self._require_sqlite("aggregate")
        if len(args) < 3:
            raise RuntimeError("[cruhon-db] @db.aggregate requires name, nargs, class.")
        self._conn.create_aggregate(str(args[0]), int(args[1]), args[2])

    def collation(self, args: list):
        """@db.collation[name; callable]  — register custom collation (sqlite)."""
        self._require_sqlite("collation")
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.collation requires name and callable.")
        self._conn.create_collation(str(args[0]), args[1])

    def dump(self, args: list):
        """@db.dump[]  → list of SQL strings that recreate the database (sqlite)."""
        self._require_sqlite("dump")
        return list(self._conn.iterdump())

    def serialize(self, args: list):
        """@db.serialize[]  → bytes snapshot of the SQLite database (py 3.11+)."""
        self._require_sqlite("serialize")
        if not hasattr(self._conn, "serialize"):
            raise RuntimeError(
                "[cruhon-db] @db.serialize requires Python 3.11+ and sqlite3 >= 3.37."
            )
        name = str(args[0]) if args else "main"
        return self._conn.serialize(name=name)

    def deserialize(self, args: list):
        """@db.deserialize[data]  — load a byte-serialized SQLite snapshot (py 3.11+)."""
        self._require_sqlite("deserialize")
        if not hasattr(self._conn, "deserialize"):
            raise RuntimeError(
                "[cruhon-db] @db.deserialize requires Python 3.11+ and sqlite3 >= 3.37."
            )
        if not args:
            raise RuntimeError("[cruhon-db] @db.deserialize requires bytes data.")
        name = str(args[1]) if len(args) > 1 else "main"
        self._conn.deserialize(args[0], name=name)

    def text_factory(self, args: list):
        """@db.text_factory[callable]  — set sqlite3 text decoding callable."""
        self._require_sqlite("text_factory")
        if not args:
            return self._conn.text_factory
        self._conn.text_factory = args[0]
        return args[0]

    def trace(self, args: list):
        """@db.trace[callable]  — set SQL trace callback (sqlite)."""
        self._require_sqlite("trace")
        fn = args[0] if args else None
        self._conn.set_trace_callback(fn)

    def progress(self, args: list):
        """@db.progress[n; callable]  — call fn every n SQLite VM opcodes."""
        self._require_sqlite("progress")
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.progress requires n and callable.")
        self._conn.set_progress_handler(args[1], int(args[0]))

    def authorizer(self, args: list):
        """@db.authorizer[callable]  — set sqlite3 authorizer callback."""
        self._require_sqlite("authorizer")
        fn = args[0] if args else None
        self._conn.set_authorizer(fn)

    def enable_ext(self, args: list):
        """@db.enable_ext[bool]  — enable or disable SQLite C extension loading."""
        self._require_sqlite("enable_ext")
        value = bool(args[0]) if args else True
        self._conn.enable_load_extension(value)

    def load_ext(self, args: list):
        """@db.load_ext[path]  — load a SQLite C extension from file path."""
        self._require_sqlite("load_ext")
        if not args:
            raise RuntimeError("[cruhon-db] @db.load_ext requires a path.")
        self._conn.load_extension(str(args[0]))

    def row_factory(self, args: list):
        """@db.row_factory[callable]  — set the row_factory on the connection."""
        self._require_conn()
        if not args:
            return self._conn.row_factory
        self._conn.row_factory = args[0]
        if self._db_type == "sqlite":
            self._cursor = self._conn.cursor()
        return args[0]

    # ── POSTGRESQL-SPECIFIC ───────────────────────────────────

    def pg_copy_from(self, args: list):
        """@db.pg_copy_from[path; table]  — COPY file data INTO table."""
        self._require_postgres("pg_copy_from")
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.pg_copy_from requires path and table.")
        with open(str(args[0]), "r") as f:
            self._cursor.copy_from(f, str(args[1]))
        self._conn.commit()

    def pg_copy_to(self, args: list):
        """@db.pg_copy_to[path; table]  — COPY table data TO file."""
        self._require_postgres("pg_copy_to")
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.pg_copy_to requires path and table.")
        with open(str(args[0]), "w") as f:
            self._cursor.copy_to(f, str(args[1]))

    def pg_copy_expert(self, args: list):
        """@db.pg_copy_expert[sql; path]  — COPY with custom SQL (read or write)."""
        self._require_postgres("pg_copy_expert")
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.pg_copy_expert requires sql and path.")
        sql = str(args[0])
        path = str(args[1])
        mode = "r" if "FROM STDIN" in sql.upper() else "w"
        with open(path, mode) as f:
            self._cursor.copy_expert(sql, f)
        if mode == "r":
            self._conn.commit()

    def pg_mogrify(self, args: list):
        """@db.pg_mogrify[sql; params]  → SQL string with params substituted (no exec)."""
        self._require_postgres("pg_mogrify")
        if not args:
            raise RuntimeError("[cruhon-db] @db.pg_mogrify requires SQL.")
        sql = str(args[0])
        params = args[1] if len(args) > 1 else None
        result = self._cursor.mogrify(sql, params)
        return result.decode() if isinstance(result, bytes) else result

    def pg_listen(self, args: list):
        """@db.pg_listen[channel]  — LISTEN to a PostgreSQL NOTIFY channel."""
        self._require_postgres("pg_listen")
        if not args:
            raise RuntimeError("[cruhon-db] @db.pg_listen requires a channel name.")
        self._cursor.execute(f"LISTEN {args[0]}")
        self._conn.commit()

    def pg_unlisten(self, args: list):
        """@db.pg_unlisten[channel]  — UNLISTEN from a channel."""
        self._require_postgres("pg_unlisten")
        if not args:
            raise RuntimeError("[cruhon-db] @db.pg_unlisten requires a channel name.")
        self._cursor.execute(f"UNLISTEN {args[0]}")
        self._conn.commit()

    def pg_notify(self, args: list):
        """@db.pg_notify[channel; payload]  — send a NOTIFY message."""
        self._require_postgres("pg_notify")
        if not args:
            raise RuntimeError("[cruhon-db] @db.pg_notify requires a channel.")
        channel = str(args[0])
        payload = str(args[1]) if len(args) > 1 else ""
        self._cursor.execute(f"NOTIFY {channel}, %s", (payload,))
        self._conn.commit()

    def pg_poll(self, args: list):
        """@db.pg_poll[]  — check for incoming async NOTIFY messages."""
        self._require_postgres("pg_poll")
        import select
        select.select([self._conn], [], [], 0)
        self._conn.poll()

    def pg_notifications(self, args: list):
        """@db.pg_notifications[]  → list of pending NOTIFY dicts."""
        self._require_postgres("pg_notifications")
        notes = []
        while self._conn.notifies:
            n = self._conn.notifies.pop(0)
            notes.append({
                "pid":     n.pid,
                "channel": n.channel,
                "payload": n.payload,
            })
        return notes

    def pg_notices(self, args: list):
        """@db.pg_notices[]  → list of server notice strings."""
        self._require_postgres("pg_notices")
        return list(self._conn.notices)

    def pg_cancel(self, args: list):
        """@db.pg_cancel[]  — cancel the currently running query."""
        self._require_postgres("pg_cancel")
        self._conn.cancel()

    def pg_reset(self, args: list):
        """@db.pg_reset[]  — reset the connection to a clean state."""
        self._require_postgres("pg_reset")
        self._conn.reset()

    def pg_pid(self, args: list):
        """@db.pg_pid[]  → PostgreSQL backend process PID."""
        self._require_postgres("pg_pid")
        return self._conn.get_backend_pid()

    def pg_param(self, args: list):
        """@db.pg_param[name]  → server parameter value (e.g. 'server_version')."""
        self._require_postgres("pg_param")
        if not args:
            raise RuntimeError("[cruhon-db] @db.pg_param requires a parameter name.")
        return self._conn.get_parameter_status(str(args[0]))

    def pg_isolation(self, args: list):
        """@db.pg_isolation[level]  — set PostgreSQL transaction isolation level."""
        self._require_postgres("pg_isolation")
        if not args:
            raise RuntimeError("[cruhon-db] @db.pg_isolation requires a level.")
        import psycopg2.extensions as ext
        levels = {
            "SERIALIZABLE":    ext.ISOLATION_LEVEL_SERIALIZABLE,
            "REPEATABLE READ": ext.ISOLATION_LEVEL_REPEATABLE_READ,
            "READ COMMITTED":  ext.ISOLATION_LEVEL_READ_COMMITTED,
            "READ UNCOMMITTED":ext.ISOLATION_LEVEL_READ_UNCOMMITTED,
            "AUTOCOMMIT":      ext.ISOLATION_LEVEL_AUTOCOMMIT,
        }
        level = str(args[0]).upper()
        self._conn.set_isolation_level(levels.get(level, int(args[0])))

    def pg_encoding(self, args: list):
        """@db.pg_encoding[enc]  — set client encoding (e.g. 'UTF8')."""
        self._require_postgres("pg_encoding")
        if not args:
            return self._conn.encoding
        self._conn.set_client_encoding(str(args[0]))

    def pg_autocommit(self, args: list):
        """@db.pg_autocommit[bool]  — set psycopg2 autocommit mode."""
        self._require_postgres("pg_autocommit")
        if not args:
            return self._conn.autocommit
        self._conn.autocommit = bool(args[0])

    def pg_status(self, args: list):
        """@db.pg_status[]  → transaction status constant int."""
        self._require_postgres("pg_status")
        return self._conn.get_transaction_status()

    def pg_server_version(self, args: list):
        """@db.pg_server_version[]  → integer version (e.g. 140001 = 14.0.1)."""
        self._require_postgres("pg_server_version")
        return self._conn.server_version

    def pg_tpc_begin(self, args: list):
        """@db.pg_tpc_begin[xid]  — begin a two-phase commit transaction."""
        self._require_postgres("pg_tpc_begin")
        if not args:
            raise RuntimeError("[cruhon-db] @db.pg_tpc_begin requires an xid.")
        xid = args[0]
        if isinstance(xid, (list, tuple)):
            xid = self._conn.xid(*xid)
        self._conn.tpc_begin(xid)

    def pg_tpc_prepare(self, args: list):
        """@db.pg_tpc_prepare[]  — prepare the two-phase commit transaction."""
        self._require_postgres("pg_tpc_prepare")
        self._conn.tpc_prepare()

    def pg_tpc_commit(self, args: list):
        """@db.pg_tpc_commit[]  — commit the prepared two-phase transaction."""
        self._require_postgres("pg_tpc_commit")
        self._conn.tpc_commit()

    def pg_tpc_rollback(self, args: list):
        """@db.pg_tpc_rollback[]  — rollback the prepared two-phase transaction."""
        self._require_postgres("pg_tpc_rollback")
        self._conn.tpc_rollback()

    def pg_tpc_recover(self, args: list):
        """@db.pg_tpc_recover[]  → list of pending two-phase transaction XIDs."""
        self._require_postgres("pg_tpc_recover")
        return self._conn.tpc_recover()

    # ── MYSQL-SPECIFIC ────────────────────────────────────────

    def my_select_db(self, args: list):
        """@db.my_select_db[name]  — switch to a different database."""
        self._require_mysql("my_select_db")
        if not args:
            raise RuntimeError("[cruhon-db] @db.my_select_db requires a database name.")
        self._conn.select_db(str(args[0]))

    def my_server_info(self, args: list):
        """@db.my_server_info[]  → MySQL server version string."""
        self._require_mysql("my_server_info")
        return self._conn.get_server_info()

    def my_thread_id(self, args: list):
        """@db.my_thread_id[]  → current connection thread ID."""
        self._require_mysql("my_thread_id")
        return self._conn.thread_id()

    def my_charset(self, args: list):
        """
        @db.my_charset[]        → current charset name
        @db.my_charset[name]    — set charset
        """
        self._require_mysql("my_charset")
        if not args:
            return getattr(self._conn, "charset", None)
        self._conn.set_charset(str(args[0]))

    def my_kill(self, args: list):
        """@db.my_kill[thread_id]  — kill a MySQL thread."""
        self._require_mysql("my_kill")
        if not args:
            raise RuntimeError("[cruhon-db] @db.my_kill requires a thread ID.")
        self._conn.kill(int(args[0]))

    def my_warnings(self, args: list):
        """@db.my_warnings[]  → list of MySQL warning dicts from last statement."""
        self._require_mysql("my_warnings")
        self._cursor.execute("SHOW WARNINGS")
        return self._cursor.fetchall()

    def my_nextset(self, args: list):
        """@db.my_nextset[]  — advance to the next MySQL result set."""
        self._require_mysql("my_nextset")
        result = self._cursor.nextset()
        if result:
            return self._store_result(self._cursor.fetchall())
        return None

    # ── ASYNC METHODS ─────────────────────────────────────────

    def _require_async_conn(self):
        if self._async_conn is None:
            raise RuntimeError(
                "[cruhon-db] No async connection. Call @db.async_connect first."
            )

    async def async_connect(self, args: list):
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_connect requires a DSN.")
        if self._async_conn is not None:
            await self.async_close([])
        dsn = str(args[0])
        db_type, kwargs = _parse_dsn(dsn)
        self._async_db_type = db_type
        if db_type == "sqlite":
            try:
                import aiosqlite
            except ImportError:
                raise RuntimeError(
                    "[cruhon-db] Async SQLite requires aiosqlite. pip install aiosqlite"
                )
            self._async_conn = await aiosqlite.connect(kwargs["database"])
            self._async_conn.row_factory = aiosqlite.Row
        elif db_type == "postgres":
            try:
                import asyncpg
            except ImportError:
                raise RuntimeError(
                    "[cruhon-db] Async PostgreSQL requires asyncpg. pip install asyncpg"
                )
            dsn_str = (
                f"postgresql://{kwargs.get('user','')}:{kwargs.get('password','')}@"
                f"{kwargs.get('host','localhost')}:{kwargs.get('port',5432)}"
                f"/{kwargs.get('database','')}"
            )
            self._async_conn = await asyncpg.connect(dsn_str)
        elif db_type == "mysql":
            try:
                import aiomysql
            except ImportError:
                raise RuntimeError(
                    "[cruhon-db] Async MySQL requires aiomysql. pip install aiomysql"
                )
            self._async_conn = await aiomysql.connect(
                host=kwargs.get("host", "localhost"),
                port=kwargs.get("port", 3306),
                user=kwargs.get("user", ""),
                password=kwargs.get("passwd", ""),
                db=kwargs.get("db", ""),
                cursorclass=aiomysql.DictCursor,
            )

    async def async_close(self, args: list):
        if self._async_cursor is not None:
            try:
                await self._async_cursor.close()
            except Exception:
                pass
            self._async_cursor = None
        if self._async_conn is not None:
            try:
                await self._async_conn.close()
            except Exception:
                pass
            self._async_conn = None
            self._async_db_type = None

    async def async_query(self, args: list):
        self._require_async_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_query requires SQL.")
        sql = str(args[0])
        params = tuple(args[1:]) if len(args) > 1 else ()
        if self._async_db_type == "sqlite":
            async with self._async_conn.execute(sql, params) as cur:
                rows = await cur.fetchall()
                if cur.description:
                    self._async_last_cols = [d[0] for d in cur.description]
            self._async_last_result = [dict(r) for r in rows]
        elif self._async_db_type == "postgres":
            rows = await self._async_conn.fetch(sql, *params)
            self._async_last_result = [dict(r) for r in rows]
            self._async_last_cols = list(rows[0].keys()) if rows else []
        elif self._async_db_type == "mysql":
            async with self._async_conn.cursor() as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()
                self._async_last_cols = [d[0] for d in cur.description] if cur.description else []
            self._async_last_result = list(rows)
        return self._async_last_result

    async def async_exec(self, args: list):
        self._require_async_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_exec requires SQL.")
        sql = str(args[0])
        params = tuple(args[1:]) if len(args) > 1 else ()
        if self._async_db_type == "sqlite":
            async with self._async_conn.execute(sql, params) as cur:
                self._async_last_id = cur.lastrowid
                self._async_last_rowcount = max(cur.rowcount or 0, 0)
            await self._async_conn.commit()
        elif self._async_db_type == "postgres":
            await self._async_conn.execute(sql, *params)
            self._async_last_id = None
        elif self._async_db_type == "mysql":
            async with self._async_conn.cursor() as cur:
                await cur.execute(sql, params)
                self._async_last_id = cur.lastrowid
                self._async_last_rowcount = max(cur.rowcount or 0, 0)
            await self._async_conn.commit()
        return self._async_last_id

    async def async_execmany(self, args: list):
        """@db.async_execmany[sql; rows]  — execute parameterized SQL for each row."""
        self._require_async_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.async_execmany requires sql and rows.")
        sql, rows = str(args[0]), args[1]
        if self._async_db_type == "sqlite":
            await self._async_conn.executemany(sql, rows)
            await self._async_conn.commit()
        elif self._async_db_type == "postgres":
            await self._async_conn.executemany(sql, rows)
        elif self._async_db_type == "mysql":
            async with self._async_conn.cursor() as cur:
                await cur.executemany(sql, rows)
            await self._async_conn.commit()

    async def async_insert(self, args: list):
        self._require_async_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.async_insert requires table and data.")
        table, data = str(args[0]), args[1]
        if not isinstance(data, dict) or not data:
            raise RuntimeError("[cruhon-db] @db.async_insert: data must be a non-empty dict.")
        cols = list(data.keys())
        vals = list(data.values())
        if self._async_db_type == "postgres":
            placeholders = ", ".join(f"${i+1}" for i in range(len(cols)))
        else:
            ph = "?" if self._async_db_type == "sqlite" else "%s"
            placeholders = ", ".join(ph for _ in cols)
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
        return await self.async_exec([sql] + vals)

    async def async_insertmany(self, args: list):
        self._require_async_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.async_insertmany requires table and rows.")
        table, rows = str(args[0]), args[1]
        if not isinstance(rows, (list, tuple)) or not rows:
            raise RuntimeError("[cruhon-db] @db.async_insertmany: rows must be non-empty list.")
        cols = list(rows[0].keys())
        if self._async_db_type == "postgres":
            placeholders = ", ".join(f"${i+1}" for i in range(len(cols)))
        else:
            ph = "?" if self._async_db_type == "sqlite" else "%s"
            placeholders = ", ".join(ph for _ in cols)
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
        param_rows = [tuple(r[c] for c in cols) for r in rows]
        await self.async_execmany([sql, param_rows])

    async def async_get(self, args: list):
        self._require_async_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.async_get requires table and where.")
        table, where = str(args[0]), str(args[1])
        params = tuple(args[2:])
        result = await self.async_query([f"SELECT * FROM {table} WHERE {where} LIMIT 1"] + list(params))
        return result[0] if result else None

    async def async_getall(self, args: list):
        self._require_async_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_getall requires a table.")
        table = str(args[0])
        if len(args) > 1:
            where = str(args[1])
            params = tuple(args[2:])
            return await self.async_query([f"SELECT * FROM {table} WHERE {where}"] + list(params))
        return await self.async_query([f"SELECT * FROM {table}"])

    async def async_begin(self, args: list):
        self._require_async_conn()
        if self._async_db_type == "sqlite":
            await self._async_conn.execute("BEGIN")
        elif self._async_db_type == "mysql":
            await self._async_conn.begin()

    async def async_commit(self, args: list):
        self._require_async_conn()
        await self._async_conn.commit()

    async def async_rollback(self, args: list):
        self._require_async_conn()
        await self._async_conn.rollback()

    def async_one(self, args: list):
        return self._async_last_result[0] if self._async_last_result else None

    def async_rows(self, args: list):
        return self._async_last_result

    def async_count(self, args: list):
        return len(self._async_last_result)

    def async_rowcount(self, args: list):
        """@db.async_rowcount[]  → rows affected by last async exec."""
        return self._async_last_rowcount

    def async_cols(self, args: list):
        """@db.async_cols[]  → column names from last async query."""
        return list(self._async_last_cols)

    # ── Async streaming cursor ────────────────────────────────

    async def async_cursor_open(self, args: list):
        """
        @db.async_cursor_open[sql; params...]
        Open a streaming cursor — does NOT fetch rows immediately.
        Use async_fetchone / async_fetchmany to iterate.
        """
        self._require_async_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_cursor_open requires SQL.")
        sql = str(args[0])
        params = tuple(args[1:]) if len(args) > 1 else ()
        if self._async_cursor is not None:
            try: await self._async_cursor.close()
            except Exception: pass
            self._async_cursor = None
        if self._async_db_type == "sqlite":
            self._async_cursor = await self._async_conn.execute(sql, params)
        elif self._async_db_type == "mysql":
            cur = await self._async_conn.cursor()
            await cur.execute(sql, params)
            self._async_cursor = cur
        elif self._async_db_type == "postgres":
            # asyncpg: requires transaction for cursor usage
            self._async_cursor = await self._async_conn.cursor(sql, *params)

    async def async_fetchone(self, args: list):
        """@db.async_fetchone[]  → next row dict from open streaming cursor, or None."""
        if self._async_cursor is None:
            raise RuntimeError(
                "[cruhon-db] No open async cursor. Call @db.async_cursor_open first."
            )
        if self._async_db_type in ("sqlite", "mysql"):
            row = await self._async_cursor.fetchone()
            if row is None:
                return None
            return dict(row) if hasattr(row, "keys") else dict(row)
        elif self._async_db_type == "postgres":
            row = await self._async_cursor.fetchrow()
            return dict(row) if row is not None else None

    async def async_fetchmany(self, args: list):
        """@db.async_fetchmany[n]  → next n row dicts from open streaming cursor."""
        if self._async_cursor is None:
            raise RuntimeError(
                "[cruhon-db] No open async cursor. Call @db.async_cursor_open first."
            )
        n = int(args[0]) if args else 1
        if self._async_db_type in ("sqlite", "mysql"):
            rows = await self._async_cursor.fetchmany(n)
            return [dict(r) if hasattr(r, "keys") else dict(r) for r in rows]
        elif self._async_db_type == "postgres":
            rows = await self._async_cursor.fetch(n)
            return [dict(r) for r in rows]

    async def async_cursor_close(self, args: list):
        """@db.async_cursor_close[]  — close the open streaming cursor."""
        if self._async_cursor is not None:
            try: await self._async_cursor.close()
            except Exception: pass
            self._async_cursor = None

    def async_in_transaction(self, args: list):
        """@db.async_in_transaction[]  → bool (aiosqlite)."""
        if self._async_conn is None:
            return False
        if self._async_db_type == "sqlite":
            return getattr(self._async_conn, "in_transaction", False)
        return None

    # ── Async aiosqlite extras ────────────────────────────────

    async def async_script(self, args: list):
        """@db.async_script[sql]  — executescript (aiosqlite)."""
        self._require_async_conn()
        if self._async_db_type != "sqlite":
            raise RuntimeError("[cruhon-db] @db.async_script is aiosqlite-only.")
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_script requires SQL.")
        await self._async_conn.executescript(str(args[0]))

    async def async_func(self, args: list):
        """@db.async_func[name; nargs; callable]  — register Python fn as SQL function (aiosqlite)."""
        self._require_async_conn()
        if self._async_db_type != "sqlite":
            raise RuntimeError("[cruhon-db] @db.async_func is aiosqlite-only.")
        if len(args) < 3:
            raise RuntimeError("[cruhon-db] @db.async_func requires name, nargs, callable.")
        self._async_conn._connection.create_function(str(args[0]), int(args[1]), args[2])

    async def async_total_changes(self, args: list):
        """@db.async_total_changes[]  → total_changes (aiosqlite)."""
        self._require_async_conn()
        if self._async_db_type != "sqlite":
            raise RuntimeError("[cruhon-db] @db.async_total_changes is aiosqlite-only.")
        return self._async_conn.total_changes

    async def async_dump(self, args: list):
        """@db.async_dump[]  → list of SQL strings (aiosqlite iterdump)."""
        self._require_async_conn()
        if self._async_db_type != "sqlite":
            raise RuntimeError("[cruhon-db] @db.async_dump is aiosqlite-only.")
        result = []
        async for line in self._async_conn.iterdump():
            result.append(line)
        return result

    # ── Async asyncpg extras ──────────────────────────────────

    async def async_fetchrow(self, args: list):
        """@db.async_fetchrow[sql; params...]  → single row dict or None (asyncpg)."""
        self._require_async_conn()
        if self._async_db_type != "postgres":
            # Fallback: use async_query and return first
            result = await self.async_query(args)
            return result[0] if result else None
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_fetchrow requires SQL.")
        sql = str(args[0])
        params = tuple(args[1:])
        row = await self._async_conn.fetchrow(sql, *params)
        return dict(row) if row is not None else None

    async def async_fetchval(self, args: list):
        """@db.async_fetchval[sql; col_index; params...]  → scalar value (asyncpg)."""
        self._require_async_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_fetchval requires SQL.")
        sql = str(args[0])
        if self._async_db_type == "postgres":
            column = int(args[1]) if len(args) > 1 and isinstance(args[1], int) else 0
            params = tuple(args[2:]) if len(args) > 2 else ()
            return await self._async_conn.fetchval(sql, *params, column=column)
        # Fallback
        result = await self.async_query(args[:1] + list(args[2:]))
        if not result:
            return None
        return list(result[0].values())[0]

    async def async_copy_from(self, args: list):
        """@db.async_copy_from[table; records]  — copy records list to table (asyncpg)."""
        self._require_async_conn()
        if self._async_db_type != "postgres":
            raise RuntimeError("[cruhon-db] @db.async_copy_from is asyncpg-only.")
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.async_copy_from requires table and records.")
        await self._async_conn.copy_records_to_table(str(args[0]), records=args[1])

    async def async_copy_to(self, args: list):
        """@db.async_copy_to[table; path]  — copy table to file (asyncpg)."""
        self._require_async_conn()
        if self._async_db_type != "postgres":
            raise RuntimeError("[cruhon-db] @db.async_copy_to is asyncpg-only.")
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.async_copy_to requires table and path.")
        with open(str(args[1]), "w") as f:
            await self._async_conn.copy_from_table(str(args[0]), output=f)

    async def async_server_version(self, args: list):
        """@db.async_server_version[]  → version info (asyncpg namedtuple or string)."""
        self._require_async_conn()
        if self._async_db_type == "postgres":
            return self._async_conn.get_server_version()
        return None

    async def async_pid(self, args: list):
        """@db.async_pid[]  → backend server PID (asyncpg)."""
        self._require_async_conn()
        if self._async_db_type == "postgres":
            return self._async_conn.get_server_pid()
        return None

    async def async_is_closed(self, args: list):
        """@db.async_is_closed[]  → bool (asyncpg)."""
        if self._async_conn is None:
            return True
        if self._async_db_type == "postgres":
            return self._async_conn.is_closed()
        return False

    async def async_terminate(self, args: list):
        """@db.async_terminate[]  — forcefully close async connection (asyncpg)."""
        self._require_async_conn()
        if self._async_db_type == "postgres":
            self._async_conn.terminate()
            self._async_conn = None
            self._async_db_type = None
        else:
            await self.async_close([])

    async def async_reset(self, args: list):
        """@db.async_reset[]  — reset async connection state."""
        self._require_async_conn()
        if self._async_db_type == "postgres":
            await self._async_conn.reset()
        elif self._async_db_type in ("sqlite", "mysql"):
            dsn = None
            if self._async_db_type == "sqlite":
                dsn = "sqlite:///" + getattr(
                    self._async_conn, "_connection", self._async_conn
                ).database if hasattr(
                    getattr(self._async_conn, "_connection", None), "database"
                ) else None
            await self.async_close([])
            if dsn:
                await self.async_connect([dsn])

    # ── Async aiomysql extras ─────────────────────────────────

    async def async_select_db(self, args: list):
        """@db.async_select_db[name]  — switch database (aiomysql)."""
        self._require_async_conn()
        if self._async_db_type != "mysql":
            raise RuntimeError("[cruhon-db] @db.async_select_db is aiomysql-only.")
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_select_db requires a database name.")
        await self._async_conn.select_db(str(args[0]))

    async def async_charset(self, args: list):
        """@db.async_charset[name]  — set character set (aiomysql)."""
        self._require_async_conn()
        if self._async_db_type != "mysql":
            raise RuntimeError("[cruhon-db] @db.async_charset is aiomysql-only.")
        if not args:
            return getattr(self._async_conn, "charset", None)
        await self._async_conn.set_charset(str(args[0]))

    async def async_ping(self, args: list):
        """@db.async_ping[]  → bool — test async connection (aiomysql)."""
        if self._async_conn is None:
            return False
        if self._async_db_type == "mysql":
            try:
                await self._async_conn.ping()
                return True
            except Exception:
                return False
        return self._async_conn is not None

    async def async_callproc(self, args: list):
        """@db.async_callproc[name; args_list]  — call stored procedure (aiomysql)."""
        self._require_async_conn()
        if self._async_db_type != "mysql":
            raise RuntimeError("[cruhon-db] @db.async_callproc is aiomysql-only.")
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_callproc requires a procedure name.")
        name = str(args[0])
        proc_args = args[1] if len(args) > 1 else []
        async with self._async_conn.cursor() as cur:
            await cur.callproc(name, proc_args)
            rows = await cur.fetchall()
        self._async_last_result = list(rows)
        return self._async_last_result

    async def async_scroll(self, args: list):
        """@db.async_scroll[n]  — scroll open async cursor (aiomysql)."""
        if self._async_cursor is None:
            raise RuntimeError(
                "[cruhon-db] No open async cursor. Call @db.async_cursor_open first."
            )
        if self._async_db_type != "mysql":
            raise RuntimeError("[cruhon-db] @db.async_scroll is aiomysql cursor-only.")
        n = int(args[0]) if args else 0
        mode = str(args[1]).strip('"\'') if len(args) > 1 else "relative"
        await self._async_cursor.scroll(n, mode=mode)


# ─────────────────────────────────────────────────────────────
# METHOD REGISTRIES
# ─────────────────────────────────────────────────────────────

_SYNC_METHODS = (
    # Connection
    "connect", "close", "ping", "reconnect", "in_transaction",
    # Connection info & raw access
    "connection", "cursor_obj", "db_type", "dsn", "closed", "conn_info",
    "server_version", "autocommit", "isolation_level", "total_changes",
    # Core exec/query
    "exec", "execmany", "query", "fetchone", "fetchmany", "fetchall",
    # CRUD
    "insert", "insertmany", "update", "delete", "get", "getall", "truncate",
    # Cursor control
    "scroll", "rownumber", "arraysize", "callproc", "nextset", "cursor_close",
    # Schema
    "create", "drop", "exists", "tables", "views",
    "schema", "indexes", "rename", "index_create", "index_drop",
    # Result access
    "rows", "one", "row", "col", "cols", "count", "rowcount", "lastid",
    # Transactions
    "begin", "commit", "rollback", "savepoint", "release", "rollback_to",
    # SQLite-specific
    "pragma", "vacuum", "backup", "restore",
    "script", "func", "aggregate", "collation", "dump",
    "serialize", "deserialize", "text_factory", "trace", "progress",
    "authorizer", "enable_ext", "load_ext", "row_factory",
    # PostgreSQL-specific
    "pg_copy_from", "pg_copy_to", "pg_copy_expert", "pg_mogrify",
    "pg_listen", "pg_unlisten", "pg_notify", "pg_poll", "pg_notifications",
    "pg_notices", "pg_cancel", "pg_reset", "pg_pid", "pg_param",
    "pg_isolation", "pg_encoding", "pg_autocommit", "pg_status",
    "pg_server_version",
    "pg_tpc_begin", "pg_tpc_prepare", "pg_tpc_commit",
    "pg_tpc_rollback", "pg_tpc_recover",
    # MySQL-specific
    "my_select_db", "my_server_info", "my_thread_id", "my_charset",
    "my_kill", "my_warnings", "my_nextset",
)

_ASYNC_METHODS = (
    # Core async
    "async_connect", "async_close",
    "async_query", "async_exec", "async_execmany",
    "async_insert", "async_insertmany",
    "async_get", "async_getall",
    "async_begin", "async_commit", "async_rollback",
    # Async result access (sync wrappers)
    "async_one", "async_rows", "async_count",
    "async_rowcount", "async_cols",
    # Streaming cursor
    "async_cursor_open", "async_fetchone", "async_fetchmany", "async_cursor_close",
    "async_in_transaction",
    # aiosqlite extras
    "async_script", "async_func", "async_total_changes", "async_dump",
    # asyncpg extras
    "async_fetchrow", "async_fetchval",
    "async_copy_from", "async_copy_to",
    "async_server_version", "async_pid", "async_is_closed",
    "async_terminate", "async_reset",
    # aiomysql extras
    "async_select_db", "async_charset", "async_ping",
    "async_callproc", "async_scroll",
)

# Sync result-accessor methods that are actually synchronous even though
# they have the async_ prefix — they just read stored state.
_ASYNC_SYNC_ACCESSORS = {
    "async_one", "async_rows", "async_count",
    "async_rowcount", "async_cols", "async_in_transaction",
}


# ─────────────────────────────────────────────────────────────
# REGISTRATION
# ─────────────────────────────────────────────────────────────

def register(api):
    api.lib("db", None)

    def _make_sync_handler(method_name: str):
        def handler(args: list) -> str:
            if args:
                return f'__ns__["db"].call("{method_name}", {", ".join(args)})'
            return f'__ns__["db"].call("{method_name}")'
        return handler

    def _make_async_handler(method_name: str):
        # Accessors that only read stored state are NOT coroutines — no await
        if method_name in _ASYNC_SYNC_ACCESSORS:
            return _make_sync_handler(method_name)
        def handler(args: list) -> str:
            if args:
                return f'(await __ns__["db"].call("{method_name}", {", ".join(args)}))'
            return f'(await __ns__["db"].call("{method_name}"))'
        return handler

    for m in _SYNC_METHODS:
        api.lib_call("db", m, _make_sync_handler(m))

    for m in _ASYNC_METHODS:
        api.lib_call("db", m, _make_async_handler(m))

    db = _DB()
    ns = api.namespace("db")
    for m in _SYNC_METHODS:
        ns.register(m, getattr(db, m))
    for m in _ASYNC_METHODS:
        ns.register(m, getattr(db, m))

    def _destroy(ns_obj):
        db.close([])
        import asyncio
        if db._async_conn is not None:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(db.async_close([]))
                else:
                    loop.run_until_complete(db.async_close([]))
            except Exception:
                pass

    ns.hook("destroy", _destroy)
