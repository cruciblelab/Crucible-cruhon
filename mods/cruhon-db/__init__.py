"""
cruhon-db — database plugin for Cruhon.

Supported backends:
  - SQLite    (built-in, zero deps)
  - PostgreSQL (psycopg2 required:  pip install psycopg2-binary)
  - MySQL     (pymysql required:    pip install pymysql)

Connection:
  @db.connect["sqlite:///data.db"]
  @db.connect["sqlite:///:memory:"]
  @db.connect["postgres://user:pass@host:5432/dbname"]
  @db.connect["mysql://user:pass@host:3306/dbname"]

Schema:
  @db.create["CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)"]
  @db.drop["users"]
  @db.exists["users"]          → True / False
  @db.tables[]                 → ["users", "posts", ...]

CRUD:
  @db.exec["INSERT INTO users VALUES (?, ?, ?)"; 1; "Alice"; 30]
  @db.insert["users"; {"name": "Alice", "age": 30}]
  @db.query["SELECT * FROM users WHERE age > ?"; 25]
  @db.update["users"; {"age": 31}; "name = ?"; "Alice"]
  @db.delete["users"; "name = ?"; "Alice"]

Result access:
  @db.rows[]                   → list of dicts from last @db.query
  @db.one[]                    → first dict from last @db.query
  @db.count[]                  → row count from last @db.query
  @db.lastid[]                 → last INSERT rowid

Transactions:
  @db.begin[]
  @db.exec["INSERT INTO users ..."]
  @db.commit[]     (or @db.rollback[] on error)

Close:
  @db.close[]
"""

from __future__ import annotations
import re
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────
# DSN PARSER
# ─────────────────────────────────────────────────────────────

def _parse_dsn(url: str):
    """
    Parse a DSN string into (db_type, connect_kwargs).

    Supported formats:
      sqlite:///path/to/file.db
      sqlite:///:memory:
      postgres://user:pass@host:5432/dbname
      postgresql://user:pass@host:5432/dbname
      mysql://user:pass@host:3306/dbname
      path/to/file.db   (bare path → SQLite)
    """
    url = url.strip()

    if url.startswith("sqlite:"):
        path = re.sub(r"^sqlite:///", "", url)
        return "sqlite", {"database": path or ":memory:"}

    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            rest = url[len(prefix):]
            m = re.match(
                r"(?:([^:@]+)(?::([^@]*))?@)?([^:/]+)(?::(\d+))?(?:/(.*))?$",
                rest,
            )
            if not m:
                raise ValueError(f"[cruhon-db] Cannot parse PostgreSQL DSN: {url!r}")
            user, password, host, port, dbname = m.groups()
            kwargs: dict = {"host": host or "localhost", "database": dbname or ""}
            if user:     kwargs["user"] = user
            if password: kwargs["password"] = password
            if port:     kwargs["port"] = int(port)
            return "postgres", kwargs

    if url.startswith("mysql://"):
        rest = url[8:]
        m = re.match(
            r"(?:([^:@]+)(?::([^@]*))?@)?([^:/]+)(?::(\d+))?(?:/(.*))?$",
            rest,
        )
        if not m:
            raise ValueError(f"[cruhon-db] Cannot parse MySQL DSN: {url!r}")
        user, password, host, port, dbname = m.groups()
        kwargs = {"host": host or "localhost", "db": dbname or ""}
        if user:     kwargs["user"] = user
        if password: kwargs["passwd"] = password
        if port:     kwargs["port"] = int(port)
        return "mysql", kwargs

    # Bare path — treat as SQLite
    return "sqlite", {"database": url}


# ─────────────────────────────────────────────────────────────
# DB CLASS
# ─────────────────────────────────────────────────────────────

class _DB:
    """
    Single database connection manager.
    One instance lives for the lifetime of a Cruhon mod session.
    Each registered method receives args as a list.
    """

    def __init__(self):
        self._conn = None
        self._cursor = None
        self._db_type: Optional[str] = None
        self._last_result: list = []
        self._last_id: Optional[Any] = None
        self._in_transaction: bool = False

    # ── Internal helpers ───────────────────────────────────────

    def _require_conn(self):
        if self._conn is None:
            raise RuntimeError(
                "[cruhon-db] No active connection. Call @db.connect first."
            )

    def _auto_commit(self):
        # SQLite opened with isolation_level=None is autocommit per-statement.
        # PostgreSQL and MySQL use implicit transactions that require an explicit commit.
        if not self._in_transaction and self._db_type in ("postgres", "mysql"):
            self._conn.commit()

    def _row_to_dict(self, row) -> dict:
        """Normalize a row from any backend to a plain dict."""
        if row is None:
            return None
        if isinstance(row, dict):
            return dict(row)
        # sqlite3.Row (has .keys())
        if hasattr(row, "keys"):
            return dict(row)
        # Tuple + cursor description (psycopg2 default cursor fallback)
        if self._cursor and hasattr(self._cursor, "description") and self._cursor.description:
            cols = [d[0] for d in self._cursor.description]
            return dict(zip(cols, row))
        return {"_": row}

    # ── Connection ─────────────────────────────────────────────

    def connect(self, args: list):
        """@db.connect[dsn]"""
        if not args:
            raise RuntimeError("[cruhon-db] @db.connect requires a DSN argument.")

        if self._conn is not None:
            self.close([])

        dsn = str(args[0])
        db_type, kwargs = _parse_dsn(dsn)
        self._db_type = db_type

        if db_type == "sqlite":
            import sqlite3
            # isolation_level=None → autocommit mode; we manage transactions explicitly
            # via BEGIN/COMMIT/ROLLBACK to avoid conflicts with Python's implicit BEGIN.
            self._conn = sqlite3.connect(kwargs["database"], isolation_level=None)
            self._conn.row_factory = sqlite3.Row
            self._cursor = self._conn.cursor()

        elif db_type == "postgres":
            try:
                import psycopg2
                import psycopg2.extras
                self._conn = psycopg2.connect(**kwargs)
                self._cursor = self._conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                )
            except ImportError:
                raise RuntimeError(
                    "[cruhon-db] PostgreSQL requires psycopg2. "
                    "Install with: pip install psycopg2-binary"
                )

        elif db_type == "mysql":
            try:
                import pymysql
                import pymysql.cursors
                kwargs["cursorclass"] = pymysql.cursors.DictCursor
                self._conn = pymysql.connect(**kwargs)
                self._cursor = self._conn.cursor()
            except ImportError:
                raise RuntimeError(
                    "[cruhon-db] MySQL requires pymysql. "
                    "Install with: pip install pymysql"
                )

        return self._conn

    def close(self, args: list):
        """@db.close[]"""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
            self._cursor = None
            self._db_type = None
            self._in_transaction = False

    # ── Core query / exec ──────────────────────────────────────

    def query(self, args: list):
        """
        @db.query[sql]
        @db.query[sql; param1; param2; ...]
        Execute a SELECT. Returns list of dicts. Also stores in last result.
        Use ? placeholders for SQLite, %s for PostgreSQL/MySQL.
        """
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.query requires a SQL argument.")

        sql = str(args[0])
        params = tuple(args[1:]) if len(args) > 1 else ()

        self._cursor.execute(sql, params)
        rows = self._cursor.fetchall()
        self._last_result = [self._row_to_dict(r) for r in rows]
        return self._last_result

    def exec(self, args: list):
        """
        @db.exec[sql]
        @db.exec[sql; param1; param2; ...]
        Execute a non-SELECT statement (INSERT, UPDATE, DELETE, DDL).
        Returns the last insert rowid (or rowcount for UPDATE/DELETE).
        """
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.exec requires a SQL argument.")

        sql = str(args[0])
        params = tuple(args[1:]) if len(args) > 1 else ()

        self._cursor.execute(sql, params)
        self._last_id = self._cursor.lastrowid
        self._auto_commit()
        return self._last_id

    # ── CRUD shortcuts ─────────────────────────────────────────

    def insert(self, args: list):
        """
        @db.insert[table; {col: val, ...}]
        Build and run an INSERT from a dict. Returns lastrowid.
        """
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError(
                "[cruhon-db] @db.insert requires two arguments: table and data dict."
            )

        table = str(args[0])
        data = args[1]
        if not isinstance(data, dict):
            raise RuntimeError(
                "[cruhon-db] @db.insert: second argument must be a dict."
            )
        if not data:
            raise RuntimeError("[cruhon-db] @db.insert: data dict is empty.")

        cols = list(data.keys())
        vals = list(data.values())
        ph = "?" if self._db_type == "sqlite" else "%s"
        placeholders = ", ".join(ph for _ in cols)
        col_str = ", ".join(cols)

        sql = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})"
        self._cursor.execute(sql, vals)
        self._last_id = self._cursor.lastrowid
        self._auto_commit()
        return self._last_id

    def update(self, args: list):
        """
        @db.update[table; {col: val, ...}; where_sql]
        @db.update[table; {col: val, ...}; where_sql; param1; ...]
        Update rows matching where_sql. Returns affected rowcount.
        """
        self._require_conn()
        if len(args) < 3:
            raise RuntimeError(
                "[cruhon-db] @db.update requires: table, data dict, where clause."
            )

        table = str(args[0])
        data = args[1]
        where = str(args[2])
        where_params = list(args[3:])

        if not isinstance(data, dict):
            raise RuntimeError("[cruhon-db] @db.update: second argument must be a dict.")

        ph = "?" if self._db_type == "sqlite" else "%s"
        set_parts = [f"{k} = {ph}" for k in data.keys()]
        sql = f"UPDATE {table} SET {', '.join(set_parts)} WHERE {where}"
        all_params = list(data.values()) + where_params

        self._cursor.execute(sql, all_params)
        rowcount = self._cursor.rowcount
        self._auto_commit()
        return rowcount

    def delete(self, args: list):
        """
        @db.delete[table; where_sql]
        @db.delete[table; where_sql; param1; ...]
        Delete rows matching where_sql. Returns affected rowcount.
        """
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError(
                "[cruhon-db] @db.delete requires: table and where clause."
            )

        table = str(args[0])
        where = str(args[1])
        params = list(args[2:])

        sql = f"DELETE FROM {table} WHERE {where}"
        self._cursor.execute(sql, params)
        rowcount = self._cursor.rowcount
        self._auto_commit()
        return rowcount

    # ── Schema helpers ─────────────────────────────────────────

    def create(self, args: list):
        """
        @db.create["CREATE TABLE IF NOT EXISTS users (...)"]
        Execute a CREATE TABLE statement.
        """
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.create requires a CREATE TABLE SQL.")
        self._cursor.execute(str(args[0]))
        self._auto_commit()

    def drop(self, args: list):
        """
        @db.drop[table]
        DROP TABLE IF EXISTS <table>.
        """
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.drop requires a table name.")
        self._cursor.execute(f"DROP TABLE IF EXISTS {args[0]}")
        self._auto_commit()

    def exists(self, args: list):
        """
        @db.exists[table]  → True if the table exists, False otherwise.
        """
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.exists requires a table name.")

        table = str(args[0])

        if self._db_type == "sqlite":
            self._cursor.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            )
        elif self._db_type == "postgres":
            self._cursor.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name=%s",
                (table,),
            )
        elif self._db_type == "mysql":
            self._cursor.execute("SHOW TABLES LIKE %s", (table,))

        return self._cursor.fetchone() is not None

    def tables(self, args: list):
        """
        @db.tables[]  → sorted list of table names.
        """
        self._require_conn()

        if self._db_type == "sqlite":
            self._cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return [dict(row)["name"] for row in self._cursor.fetchall()]

        elif self._db_type == "postgres":
            self._cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' ORDER BY table_name"
            )
            rows = self._cursor.fetchall()
            return [r["table_name"] for r in rows]

        elif self._db_type == "mysql":
            self._cursor.execute("SHOW TABLES")
            rows = self._cursor.fetchall()
            # DictCursor key is "Tables_in_<dbname>"
            return [list(r.values())[0] for r in rows]

        return []

    # ── Result accessors ───────────────────────────────────────

    def rows(self, args: list):
        """
        @db.rows[]         → list of dicts from last @db.query
        @db.rows[result]   → pass-through (returns the given result unchanged)
        """
        return args[0] if args else self._last_result

    def one(self, args: list):
        """
        @db.one[]          → first row dict from last @db.query (or None)
        @db.one[result]    → first row dict from given result
        """
        result = args[0] if args else self._last_result
        if isinstance(result, (list, tuple)):
            return result[0] if result else None
        return result

    def count(self, args: list):
        """
        @db.count[]        → number of rows in last @db.query result
        @db.count[result]  → number of rows in given result
        """
        result = args[0] if args else self._last_result
        if isinstance(result, (list, tuple)):
            return len(result)
        return 0

    def lastid(self, args: list):
        """@db.lastid[]  → rowid of the last INSERT."""
        return self._last_id

    # ── Transactions ───────────────────────────────────────────

    def begin(self, args: list):
        """@db.begin[]  → begin an explicit transaction."""
        self._require_conn()
        if self._in_transaction:
            return  # already in one — no-op
        self._in_transaction = True
        if self._db_type == "sqlite":
            self._cursor.execute("BEGIN")
        elif self._db_type == "postgres":
            # psycopg2 auto-begins on the first DML; explicit savepoint not needed.
            # Setting autocommit=False (default) means a transaction is already open.
            pass
        elif self._db_type == "mysql":
            self._cursor.execute("START TRANSACTION")

    def commit(self, args: list):
        """@db.commit[]  → commit the current transaction."""
        self._require_conn()
        self._conn.commit()
        self._in_transaction = False

    def rollback(self, args: list):
        """@db.rollback[]  → roll back the current transaction."""
        self._require_conn()
        self._conn.rollback()
        self._in_transaction = False


# ─────────────────────────────────────────────────────────────
# ALL REGISTERED METHOD NAMES
# ─────────────────────────────────────────────────────────────

_METHODS = (
    "connect", "close",
    "query", "exec",
    "insert", "update", "delete",
    "create", "drop", "exists", "tables",
    "rows", "one", "count", "lastid",
    "begin", "commit", "rollback",
)


# ─────────────────────────────────────────────────────────────
# REGISTRATION
# ─────────────────────────────────────────────────────────────

def register(api):
    # Register 'db' as a lib namespace — no Python import needed at file level.
    # The transpiler sees @db.method[...] and routes it through LibCallNode.
    api.lib("db", None)

    # Each lib_call handler generates:  __ns__["db"].call("method", arg1, arg2, ...)
    def _make_handler(method_name: str):
        def handler(args: list) -> str:
            if args:
                args_str = ", ".join(args)
                return f'__ns__["db"].call("{method_name}", {args_str})'
            return f'__ns__["db"].call("{method_name}")'
        return handler

    for m in _METHODS:
        api.lib_call("db", m, _make_handler(m))

    # One _DB instance per Cruhon session (created fresh each run via the
    # namespace init/destroy lifecycle).
    db = _DB()

    # Register namespace — the runtime dispatch table
    ns = api.namespace("db")
    for m in _METHODS:
        ns.register(m, getattr(db, m))

    # Auto-close after each script execution
    ns.hook("destroy", lambda _ns: db.close([]))
