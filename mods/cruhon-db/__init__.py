"""
cruhon-db — comprehensive database plugin for Cruhon.

Sync backends:  SQLite (built-in), PostgreSQL (psycopg2), MySQL (pymysql)
Async backends: SQLite (aiosqlite), PostgreSQL (asyncpg), MySQL (aiomysql)

=== CONNECTION ===
  @db.connect["sqlite:///data.db"]
  @db.connect["sqlite:///:memory:"]
  @db.connect["postgres://user:pass@host:5432/dbname"]
  @db.connect["mysql://user:pass@host:3306/dbname"]
  @db.close[]
  @db.ping[]                      → bool — connection alive?
  @db.reconnect[]                 — reconnect using same DSN
  @db.in_transaction[]            → bool

=== CORE EXEC / QUERY ===
  @db.exec[sql; params...]        — INSERT/UPDATE/DELETE/DDL, returns lastrowid
  @db.execmany[sql; rows_list]    — bulk parameterized SQL
  @db.query[sql; params...]       — SELECT, stores result, returns list of dicts
  @db.fetchone[]                  → next row from open cursor (or None)
  @db.fetchmany[n]                → next n rows from open cursor
  @db.fetchall[]                  → alias: re-fetch all from open cursor

=== CRUD SHORTCUTS ===
  @db.insert[table; {col: val}]               → lastrowid
  @db.insertmany[table; [{...}, ...]]         — bulk dict-list INSERT
  @db.update[table; {col: val}; where; params...]  → rowcount
  @db.delete[table; where; params...]              → rowcount
  @db.get[table; where; params...]            → first matching row dict or None
  @db.getall[table]                           → all rows list
  @db.getall[table; where; params...]         → filtered rows list
  @db.truncate[table]                         — delete all rows (TRUNCATE or DELETE)

=== SCHEMA ===
  @db.create[sql]                — CREATE TABLE (full SQL)
  @db.drop[table]                — DROP TABLE IF EXISTS
  @db.exists[table]              → bool
  @db.tables[]                   → sorted list of table names
  @db.views[]                    → sorted list of view names
  @db.schema[table]              → list of {name, type, nullable, default, pk}
  @db.indexes[table]             → list of index info dicts
  @db.rename[old; new]           — rename a table
  @db.index_create[table; col]   — CREATE INDEX IF NOT EXISTS
  @db.index_drop[index_name]     — DROP INDEX IF EXISTS

=== RESULT ACCESS ===
  @db.rows[]                     → last query result (list of dicts)
  @db.rows[result]               → pass-through
  @db.one[]                      → first row dict or None
  @db.one[result]                → first row of given list
  @db.row[n]                     → nth row dict (0-indexed) or None
  @db.col[name]                  → named column from first row
  @db.cols[]                     → list of column names from last query
  @db.count[]                    → len of last query result
  @db.count[result]              → len of given list
  @db.rowcount[]                 → rows affected by last exec/update/delete
  @db.lastid[]                   → last INSERT rowid

=== TRANSACTIONS ===
  @db.begin[]
  @db.commit[]
  @db.rollback[]
  @db.savepoint[name]            — SAVEPOINT name
  @db.release[name]              — RELEASE SAVEPOINT name
  @db.rollback_to[name]          — ROLLBACK TO SAVEPOINT name

=== SQLITE-SPECIFIC ===
  @db.pragma[name]               → current PRAGMA value
  @db.pragma[name; value]        — set a PRAGMA
  @db.vacuum[]                   — VACUUM the SQLite database
  @db.backup[path]               — backup database to file (SQLite only)
  @db.restore[path]              — connect to an on-disk SQLite file (alias for connect)

=== ASYNC COMMANDS (use inside @async[main]...@end) ===
  @db.async_connect["sqlite:///..."]   — aiosqlite / asyncpg / aiomysql
  @db.async_close[]
  @db.async_query[sql; params...]      → list of dicts
  @db.async_exec[sql; params...]       → lastrowid
  @db.async_insert[table; data]        → lastrowid
  @db.async_insertmany[table; rows]
  @db.async_get[table; where; params...] → first row dict or None
  @db.async_getall[table]               → all rows
  @db.async_getall[table; where; params...]
  @db.async_begin[]
  @db.async_commit[]
  @db.async_rollback[]
  @db.async_one[]                       → first row of last async result
  @db.async_rows[]                      → last async result list
  @db.async_count[]                     → count of last async result
"""

from __future__ import annotations
import re
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────
# DSN PARSER
# ─────────────────────────────────────────────────────────────

def _parse_dsn(url: str):
    """
    Parse a database DSN into (db_type, connect_kwargs).

    Supported:
      sqlite:///path/to/file.db  |  sqlite:///:memory:
      postgres://user:pass@host:port/dbname
      postgresql://user:pass@host:port/dbname
      mysql://user:pass@host:port/dbname
      bare path  → treated as SQLite file
    """
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

    # Bare path → SQLite
    return "sqlite", {"database": url}


# ─────────────────────────────────────────────────────────────
# SYNC DB CLASS
# ─────────────────────────────────────────────────────────────

class _DB:
    """
    Synchronous database connection + query manager.
    One instance lives for the lifetime of a Cruhon mod session.
    Each method receives args as a list; async methods return coroutines.
    """

    def __init__(self):
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
        self._async_db_type: Optional[str] = None
        self._async_last_result: list = []
        self._async_last_id: Optional[Any] = None

    # ── Internal helpers ───────────────────────────────────────

    def _require_conn(self):
        if self._conn is None:
            raise RuntimeError(
                "[cruhon-db] No active connection. Call @db.connect first."
            )

    def _auto_commit(self):
        # SQLite with isolation_level=None is autocommit per-statement.
        # PostgreSQL and MySQL use implicit transactions requiring explicit commit.
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
        """Normalize, store, and return result list. Also updates _last_cols."""
        self._last_result = [self._row_to_dict(r) for r in rows]
        if self._cursor and self._cursor.description:
            self._last_cols = [d[0] for d in self._cursor.description]
        elif self._last_result:
            self._last_cols = list(self._last_result[0].keys())
        else:
            self._last_cols = []
        return self._last_result

    # ── Connection ─────────────────────────────────────────────

    def connect(self, args: list):
        """@db.connect[dsn]"""
        if not args:
            raise RuntimeError("[cruhon-db] @db.connect requires a DSN argument.")
        if self._conn is not None:
            self.close([])

        dsn = str(args[0])
        self._dsn = dsn
        db_type, kwargs = _parse_dsn(dsn)
        self._db_type = db_type

        if db_type == "sqlite":
            import sqlite3
            # isolation_level=None: autocommit; we manage BEGIN/COMMIT explicitly.
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
                    "Install: pip install psycopg2-binary"
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
                    "Install: pip install pymysql"
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

    def ping(self, args: list):
        """@db.ping[]  → True if connection is alive, False otherwise."""
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
        """@db.reconnect[]  — close and reopen using the same DSN."""
        if not self._dsn:
            raise RuntimeError("[cruhon-db] No previous DSN stored for reconnect.")
        self.connect([self._dsn])

    def in_transaction(self, args: list):
        """@db.in_transaction[]  → bool"""
        return self._in_transaction

    # ── Core exec / query ──────────────────────────────────────

    def exec(self, args: list):
        """
        @db.exec[sql; params...]
        Execute a non-SELECT statement. Returns lastrowid (or 0 for DDL).
        """
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.exec requires a SQL argument.")
        sql = str(args[0])
        params = tuple(args[1:]) if len(args) > 1 else ()
        self._cursor.execute(sql, params)
        self._last_id = self._cursor.lastrowid
        self._last_rowcount = self._cursor.rowcount if self._cursor.rowcount >= 0 else 0
        self._auto_commit()
        return self._last_id

    def execmany(self, args: list):
        """
        @db.execmany[sql; rows_list]
        Execute SQL for each item in rows_list (list of tuples or dicts).
        """
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError(
                "[cruhon-db] @db.execmany requires sql and rows_list arguments."
            )
        sql = str(args[0])
        rows = args[1]
        if not isinstance(rows, (list, tuple)):
            raise RuntimeError("[cruhon-db] @db.execmany: rows_list must be a list.")
        self._cursor.executemany(sql, rows)
        self._last_rowcount = self._cursor.rowcount if self._cursor.rowcount >= 0 else 0
        self._auto_commit()

    def query(self, args: list):
        """
        @db.query[sql; params...]
        Execute a SELECT. Stores and returns list of dicts.
        """
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.query requires a SQL argument.")
        sql = str(args[0])
        params = tuple(args[1:]) if len(args) > 1 else ()
        self._cursor.execute(sql, params)
        return self._store_result(self._cursor.fetchall())

    def fetchone(self, args: list):
        """@db.fetchone[]  → next row dict from open cursor, or None."""
        self._require_conn()
        row = self._cursor.fetchone()
        return self._row_to_dict(row)

    def fetchmany(self, args: list):
        """@db.fetchmany[n]  → list of next n row dicts from open cursor."""
        self._require_conn()
        n = int(args[0]) if args else 1
        rows = self._cursor.fetchmany(n)
        return [self._row_to_dict(r) for r in rows]

    def fetchall(self, args: list):
        """@db.fetchall[]  → all remaining rows from open cursor as list of dicts."""
        self._require_conn()
        return self._store_result(self._cursor.fetchall())

    # ── CRUD shortcuts ─────────────────────────────────────────

    def insert(self, args: list):
        """@db.insert[table; {col: val}]  → lastrowid."""
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError(
                "[cruhon-db] @db.insert requires table and data dict."
            )
        table = str(args[0])
        data = args[1]
        if not isinstance(data, dict):
            raise RuntimeError("[cruhon-db] @db.insert: second argument must be a dict.")
        if not data:
            raise RuntimeError("[cruhon-db] @db.insert: data dict is empty.")
        cols = list(data.keys())
        vals = list(data.values())
        ph = "?" if self._db_type == "sqlite" else "%s"
        sql = (
            f"INSERT INTO {table} ({', '.join(cols)}) "
            f"VALUES ({', '.join(ph for _ in cols)})"
        )
        self._cursor.execute(sql, vals)
        self._last_id = self._cursor.lastrowid
        self._last_rowcount = 1
        self._auto_commit()
        return self._last_id

    def insertmany(self, args: list):
        """
        @db.insertmany[table; [{col: val}, ...]]
        Bulk INSERT a list of dicts. All dicts must have identical keys.
        """
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError(
                "[cruhon-db] @db.insertmany requires table and rows_list."
            )
        table = str(args[0])
        rows = args[1]
        if not isinstance(rows, (list, tuple)) or not rows:
            raise RuntimeError(
                "[cruhon-db] @db.insertmany: rows_list must be a non-empty list of dicts."
            )
        if not isinstance(rows[0], dict):
            raise RuntimeError("[cruhon-db] @db.insertmany: each row must be a dict.")
        cols = list(rows[0].keys())
        ph = "?" if self._db_type == "sqlite" else "%s"
        sql = (
            f"INSERT INTO {table} ({', '.join(cols)}) "
            f"VALUES ({', '.join(ph for _ in cols)})"
        )
        param_rows = [tuple(r[c] for c in cols) for r in rows]
        self._cursor.executemany(sql, param_rows)
        self._last_rowcount = len(rows)
        self._auto_commit()

    def update(self, args: list):
        """@db.update[table; {col: val}; where; params...]  → rowcount."""
        self._require_conn()
        if len(args) < 3:
            raise RuntimeError(
                "[cruhon-db] @db.update requires table, data dict, and where clause."
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
        self._cursor.execute(sql, list(data.values()) + where_params)
        self._last_rowcount = self._cursor.rowcount if self._cursor.rowcount >= 0 else 0
        self._auto_commit()
        return self._last_rowcount

    def delete(self, args: list):
        """@db.delete[table; where; params...]  → rowcount."""
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError(
                "[cruhon-db] @db.delete requires table and where clause."
            )
        table = str(args[0])
        where = str(args[1])
        params = list(args[2:])
        sql = f"DELETE FROM {table} WHERE {where}"
        self._cursor.execute(sql, params)
        self._last_rowcount = self._cursor.rowcount if self._cursor.rowcount >= 0 else 0
        self._auto_commit()
        return self._last_rowcount

    def get(self, args: list):
        """
        @db.get[table; where; params...]  → first matching row dict or None.
        Stores result in last-result (single-item list or empty).
        """
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.get requires table and where clause.")
        table = str(args[0])
        where = str(args[1])
        params = tuple(args[2:])
        sql = f"SELECT * FROM {table} WHERE {where} LIMIT 1"
        self._cursor.execute(sql, params)
        row = self._cursor.fetchone()
        result = [self._row_to_dict(row)] if row is not None else []
        self._store_result(result)
        return result[0] if result else None

    def getall(self, args: list):
        """
        @db.getall[table]                → all rows
        @db.getall[table; where; params...] → filtered rows
        """
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.getall requires a table name.")
        table = str(args[0])
        if len(args) > 1:
            where = str(args[1])
            params = tuple(args[2:])
            sql = f"SELECT * FROM {table} WHERE {where}"
        else:
            sql = f"SELECT * FROM {table}"
            params = ()
        self._cursor.execute(sql, params)
        return self._store_result(self._cursor.fetchall())

    def truncate(self, args: list):
        """@db.truncate[table]  — remove all rows from table."""
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.truncate requires a table name.")
        table = str(args[0])
        if self._db_type == "sqlite":
            self._cursor.execute(f"DELETE FROM {table}")
        else:
            self._cursor.execute(f"TRUNCATE TABLE {table}")
        self._auto_commit()

    # ── Schema helpers ─────────────────────────────────────────

    def create(self, args: list):
        """@db.create[sql]  — execute a CREATE TABLE statement."""
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.create requires CREATE TABLE SQL.")
        self._cursor.execute(str(args[0]))
        self._auto_commit()

    def drop(self, args: list):
        """@db.drop[table]  — DROP TABLE IF EXISTS."""
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.drop requires a table name.")
        self._cursor.execute(f"DROP TABLE IF EXISTS {args[0]}")
        self._auto_commit()

    def exists(self, args: list):
        """@db.exists[table]  → True if table exists, False otherwise."""
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
                "WHERE table_schema='public' AND table_name=%s",
                (table,),
            )
        elif self._db_type == "mysql":
            self._cursor.execute("SHOW TABLES LIKE %s", (table,))
        return self._cursor.fetchone() is not None

    def tables(self, args: list):
        """@db.tables[]  → sorted list of table names."""
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
        """@db.views[]  → sorted list of view names."""
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
        """
        @db.schema[table]
        Returns list of dicts: {name, type, nullable, default, pk}.
        """
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.schema requires a table name.")
        table = str(args[0])
        if self._db_type == "sqlite":
            self._cursor.execute(f"PRAGMA table_info({table})")
            cols = []
            for row in self._cursor.fetchall():
                r = dict(row)
                cols.append({
                    "name":     r["name"],
                    "type":     r["type"],
                    "nullable": not r["notnull"],
                    "default":  r["dflt_value"],
                    "pk":       bool(r["pk"]),
                })
            return cols
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
        """
        @db.indexes[table]
        Returns list of index info dicts for the given table.
        """
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
                result.append({
                    "name":    idx["name"],
                    "unique":  bool(idx["unique"]),
                    "columns": cols,
                })
            return result
        elif self._db_type == "postgres":
            self._cursor.execute(
                "SELECT indexname, indexdef FROM pg_indexes "
                "WHERE tablename=%s ORDER BY indexname",
                (table,),
            )
            return [{"name": r["indexname"], "def": r["indexdef"]}
                    for r in self._cursor.fetchall()]
        elif self._db_type == "mysql":
            self._cursor.execute(f"SHOW INDEX FROM {table}")
            return self._cursor.fetchall()
        return []

    def rename(self, args: list):
        """@db.rename[old_table; new_table]  — rename a table."""
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.rename requires old and new table names.")
        old, new = str(args[0]), str(args[1])
        if self._db_type == "mysql":
            self._cursor.execute(f"RENAME TABLE {old} TO {new}")
        else:
            self._cursor.execute(f"ALTER TABLE {old} RENAME TO {new}")
        self._auto_commit()

    def index_create(self, args: list):
        """@db.index_create[table; col]  — CREATE INDEX IF NOT EXISTS."""
        self._require_conn()
        if len(args) < 2:
            raise RuntimeError(
                "[cruhon-db] @db.index_create requires table and column."
            )
        table, col = str(args[0]), str(args[1])
        idx_name = f"idx_{table}_{col}"
        if self._db_type == "sqlite":
            self._cursor.execute(
                f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({col})"
            )
        elif self._db_type == "postgres":
            self._cursor.execute(
                f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({col})"
            )
        elif self._db_type == "mysql":
            # MySQL doesn't support IF NOT EXISTS on CREATE INDEX before 8.0
            try:
                self._cursor.execute(
                    f"CREATE INDEX {idx_name} ON {table}({col})"
                )
            except Exception:
                pass
        self._auto_commit()

    def index_drop(self, args: list):
        """@db.index_drop[index_name]  — DROP INDEX IF EXISTS."""
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.index_drop requires an index name.")
        idx = str(args[0])
        if self._db_type == "sqlite":
            self._cursor.execute(f"DROP INDEX IF EXISTS {idx}")
        elif self._db_type == "postgres":
            self._cursor.execute(f"DROP INDEX IF EXISTS {idx}")
        elif self._db_type == "mysql":
            # MySQL needs the table name — skip silently if not provided
            raise RuntimeError(
                "[cruhon-db] MySQL @db.index_drop requires format: "
                "ALTER TABLE <table> DROP INDEX <idx>. Use @db.exec directly."
            )
        self._auto_commit()

    # ── Result access ──────────────────────────────────────────

    def rows(self, args: list):
        """@db.rows[]  → last result; @db.rows[result]  → pass-through."""
        return args[0] if args else self._last_result

    def one(self, args: list):
        """@db.one[] / @db.one[result]  → first row dict or None."""
        result = args[0] if args else self._last_result
        if isinstance(result, (list, tuple)):
            return result[0] if result else None
        return result

    def row(self, args: list):
        """@db.row[n]  → nth row dict (0-indexed) from last result, or None."""
        n = int(args[0]) if args else 0
        if 0 <= n < len(self._last_result):
            return self._last_result[n]
        return None

    def col(self, args: list):
        """@db.col[name]  → value of named column from first row of last result."""
        if not args:
            raise RuntimeError("[cruhon-db] @db.col requires a column name.")
        if not self._last_result:
            return None
        return self._last_result[0].get(str(args[0]))

    def cols(self, args: list):
        """@db.cols[]  → list of column names from the last query."""
        return list(self._last_cols)

    def count(self, args: list):
        """@db.count[] → len of last result; @db.count[result] → len of given list."""
        result = args[0] if args else self._last_result
        return len(result) if isinstance(result, (list, tuple)) else 0

    def rowcount(self, args: list):
        """@db.rowcount[]  → rows affected by last exec / update / delete."""
        return self._last_rowcount

    def lastid(self, args: list):
        """@db.lastid[]  → rowid of the last INSERT."""
        return self._last_id

    # ── Transactions ───────────────────────────────────────────

    def begin(self, args: list):
        """@db.begin[]  → start an explicit transaction."""
        self._require_conn()
        if self._in_transaction:
            return
        self._in_transaction = True
        if self._db_type == "sqlite":
            self._cursor.execute("BEGIN")
        elif self._db_type == "mysql":
            self._cursor.execute("START TRANSACTION")
        # psycopg2: transaction is already open implicitly

    def commit(self, args: list):
        """@db.commit[]"""
        self._require_conn()
        self._conn.commit()
        self._in_transaction = False

    def rollback(self, args: list):
        """@db.rollback[]"""
        self._require_conn()
        self._conn.rollback()
        self._in_transaction = False

    def savepoint(self, args: list):
        """@db.savepoint[name]  — create a named savepoint."""
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.savepoint requires a name.")
        self._cursor.execute(f"SAVEPOINT {args[0]}")

    def release(self, args: list):
        """@db.release[name]  — release a named savepoint."""
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.release requires a savepoint name.")
        if self._db_type == "mysql":
            self._cursor.execute(f"RELEASE SAVEPOINT {args[0]}")
        else:
            self._cursor.execute(f"RELEASE SAVEPOINT {args[0]}")

    def rollback_to(self, args: list):
        """@db.rollback_to[name]  — rollback to a named savepoint."""
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.rollback_to requires a savepoint name.")
        if self._db_type == "mysql":
            self._cursor.execute(f"ROLLBACK TO SAVEPOINT {args[0]}")
        else:
            self._cursor.execute(f"ROLLBACK TO SAVEPOINT {args[0]}")

    # ── SQLite-specific ────────────────────────────────────────

    def pragma(self, args: list):
        """
        @db.pragma[name]          → current value
        @db.pragma[name; value]   — set value
        """
        self._require_conn()
        if not args:
            raise RuntimeError("[cruhon-db] @db.pragma requires a PRAGMA name.")
        name = str(args[0])
        if len(args) > 1:
            val = args[1]
            self._cursor.execute(f"PRAGMA {name} = {val}")
            return val
        else:
            self._cursor.execute(f"PRAGMA {name}")
            row = self._cursor.fetchone()
            return dict(row)[name] if row is not None else None

    def vacuum(self, args: list):
        """@db.vacuum[]  — VACUUM the SQLite database."""
        self._require_conn()
        if self._db_type != "sqlite":
            raise RuntimeError("[cruhon-db] @db.vacuum is only supported for SQLite.")
        self._cursor.execute("VACUUM")

    def backup(self, args: list):
        """
        @db.backup[path]
        Backup the current SQLite database to a file using the sqlite3 backup API.
        """
        self._require_conn()
        if self._db_type != "sqlite":
            raise RuntimeError("[cruhon-db] @db.backup is only supported for SQLite.")
        if not args:
            raise RuntimeError("[cruhon-db] @db.backup requires a destination path.")
        import sqlite3
        dest = sqlite3.connect(str(args[0]))
        self._conn.backup(dest)
        dest.close()

    def restore(self, args: list):
        """
        @db.restore[path]
        Connect to a SQLite file (shorthand for @db.connect["sqlite:///path"]).
        """
        if not args:
            raise RuntimeError("[cruhon-db] @db.restore requires a file path.")
        self.connect([f"sqlite:///{args[0]}"])

    # ── Async methods ──────────────────────────────────────────

    async def async_connect(self, args: list):
        """@db.async_connect[dsn]  — open async connection."""
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
                    "[cruhon-db] Async SQLite requires aiosqlite. "
                    "Install: pip install aiosqlite"
                )
            self._async_conn = await aiosqlite.connect(kwargs["database"])
            self._async_conn.row_factory = aiosqlite.Row
        elif db_type == "postgres":
            try:
                import asyncpg
            except ImportError:
                raise RuntimeError(
                    "[cruhon-db] Async PostgreSQL requires asyncpg. "
                    "Install: pip install asyncpg"
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
                    "[cruhon-db] Async MySQL requires aiomysql. "
                    "Install: pip install aiomysql"
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
        """@db.async_close[]"""
        if self._async_conn is not None:
            try:
                if self._async_db_type in ("sqlite", "postgres"):
                    await self._async_conn.close()
                else:
                    self._async_conn.close()
            except Exception:
                pass
            self._async_conn = None
            self._async_db_type = None

    async def async_query(self, args: list):
        """@db.async_query[sql; params...]  → list of dicts."""
        if self._async_conn is None:
            raise RuntimeError(
                "[cruhon-db] No async connection. Call @db.async_connect first."
            )
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_query requires a SQL argument.")
        sql = str(args[0])
        params = tuple(args[1:]) if len(args) > 1 else ()
        if self._async_db_type == "sqlite":
            async with self._async_conn.execute(sql, params) as cur:
                rows = await cur.fetchall()
            self._async_last_result = [dict(r) for r in rows]
        elif self._async_db_type == "postgres":
            rows = await self._async_conn.fetch(sql, *params)
            self._async_last_result = [dict(r) for r in rows]
        elif self._async_db_type == "mysql":
            async with self._async_conn.cursor() as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()
            self._async_last_result = list(rows)
        return self._async_last_result

    async def async_exec(self, args: list):
        """@db.async_exec[sql; params...]  → lastrowid."""
        if self._async_conn is None:
            raise RuntimeError(
                "[cruhon-db] No async connection. Call @db.async_connect first."
            )
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_exec requires a SQL argument.")
        sql = str(args[0])
        params = tuple(args[1:]) if len(args) > 1 else ()
        if self._async_db_type == "sqlite":
            async with self._async_conn.execute(sql, params) as cur:
                self._async_last_id = cur.lastrowid
            await self._async_conn.commit()
        elif self._async_db_type == "postgres":
            await self._async_conn.execute(sql, *params)
            self._async_last_id = None
        elif self._async_db_type == "mysql":
            async with self._async_conn.cursor() as cur:
                await cur.execute(sql, params)
                self._async_last_id = cur.lastrowid
            await self._async_conn.commit()
        return self._async_last_id

    async def async_insert(self, args: list):
        """@db.async_insert[table; {col: val}]  → lastrowid."""
        if self._async_conn is None:
            raise RuntimeError(
                "[cruhon-db] No async connection. Call @db.async_connect first."
            )
        if len(args) < 2:
            raise RuntimeError(
                "[cruhon-db] @db.async_insert requires table and data dict."
            )
        table = str(args[0])
        data = args[1]
        if not isinstance(data, dict) or not data:
            raise RuntimeError("[cruhon-db] @db.async_insert: data must be a non-empty dict.")
        cols = list(data.keys())
        vals = list(data.values())
        ph = "?" if self._async_db_type == "sqlite" else (
            ", ".join(f"${i+1}" for i in range(len(cols)))
            if self._async_db_type == "postgres" else "%s"
        )
        if self._async_db_type == "postgres":
            placeholders = ", ".join(f"${i+1}" for i in range(len(cols)))
        else:
            placeholders = ", ".join("?" if self._async_db_type == "sqlite" else "%s"
                                     for _ in cols)
        sql = (
            f"INSERT INTO {table} ({', '.join(cols)}) "
            f"VALUES ({placeholders})"
        )
        return await self.async_exec([sql] + vals)

    async def async_insertmany(self, args: list):
        """@db.async_insertmany[table; [{col: val}, ...]]  — bulk async INSERT."""
        if self._async_conn is None:
            raise RuntimeError(
                "[cruhon-db] No async connection. Call @db.async_connect first."
            )
        if len(args) < 2:
            raise RuntimeError(
                "[cruhon-db] @db.async_insertmany requires table and rows list."
            )
        table = str(args[0])
        rows = args[1]
        if not isinstance(rows, (list, tuple)) or not rows:
            raise RuntimeError(
                "[cruhon-db] @db.async_insertmany: rows must be a non-empty list of dicts."
            )
        cols = list(rows[0].keys())
        if self._async_db_type == "postgres":
            placeholders = ", ".join(f"${i+1}" for i in range(len(cols)))
        else:
            ph = "?" if self._async_db_type == "sqlite" else "%s"
            placeholders = ", ".join(ph for _ in cols)
        sql = (
            f"INSERT INTO {table} ({', '.join(cols)}) "
            f"VALUES ({placeholders})"
        )
        param_rows = [tuple(r[c] for c in cols) for r in rows]
        if self._async_db_type == "sqlite":
            await self._async_conn.executemany(sql, param_rows)
            await self._async_conn.commit()
        elif self._async_db_type == "postgres":
            await self._async_conn.executemany(sql, param_rows)
        elif self._async_db_type == "mysql":
            async with self._async_conn.cursor() as cur:
                await cur.executemany(sql, param_rows)
            await self._async_conn.commit()

    async def async_get(self, args: list):
        """@db.async_get[table; where; params...]  → first row dict or None."""
        if self._async_conn is None:
            raise RuntimeError(
                "[cruhon-db] No async connection. Call @db.async_connect first."
            )
        if len(args) < 2:
            raise RuntimeError("[cruhon-db] @db.async_get requires table and where clause.")
        table, where = str(args[0]), str(args[1])
        params = tuple(args[2:])
        sql = f"SELECT * FROM {table} WHERE {where} LIMIT 1"
        result = await self.async_query([sql] + list(params))
        return result[0] if result else None

    async def async_getall(self, args: list):
        """
        @db.async_getall[table]
        @db.async_getall[table; where; params...]
        """
        if self._async_conn is None:
            raise RuntimeError(
                "[cruhon-db] No async connection. Call @db.async_connect first."
            )
        if not args:
            raise RuntimeError("[cruhon-db] @db.async_getall requires a table name.")
        table = str(args[0])
        if len(args) > 1:
            where = str(args[1])
            params = tuple(args[2:])
            sql = f"SELECT * FROM {table} WHERE {where}"
        else:
            sql = f"SELECT * FROM {table}"
            params = ()
        return await self.async_query([sql] + list(params))

    async def async_begin(self, args: list):
        """@db.async_begin[]"""
        if self._async_conn is None:
            raise RuntimeError(
                "[cruhon-db] No async connection. Call @db.async_connect first."
            )
        if self._async_db_type == "sqlite":
            await self._async_conn.execute("BEGIN")
        elif self._async_db_type == "mysql":
            await self._async_conn.begin()

    async def async_commit(self, args: list):
        """@db.async_commit[]"""
        if self._async_conn is None:
            raise RuntimeError(
                "[cruhon-db] No async connection. Call @db.async_connect first."
            )
        await self._async_conn.commit()

    async def async_rollback(self, args: list):
        """@db.async_rollback[]"""
        if self._async_conn is None:
            raise RuntimeError(
                "[cruhon-db] No async connection. Call @db.async_connect first."
            )
        await self._async_conn.rollback()

    def async_one(self, args: list):
        """@db.async_one[]  → first row of last async query result."""
        return self._async_last_result[0] if self._async_last_result else None

    def async_rows(self, args: list):
        """@db.async_rows[]  → last async query result (list of dicts)."""
        return self._async_last_result

    def async_count(self, args: list):
        """@db.async_count[]  → row count of last async query result."""
        return len(self._async_last_result)


# ─────────────────────────────────────────────────────────────
# ALL REGISTERED METHOD NAMES
# ─────────────────────────────────────────────────────────────

# Sync methods — generate:  __ns__["db"].call("method", args...)
_SYNC_METHODS = (
    "connect", "close", "ping", "reconnect", "in_transaction",
    "exec", "execmany", "query", "fetchone", "fetchmany", "fetchall",
    "insert", "insertmany", "update", "delete", "get", "getall", "truncate",
    "create", "drop", "exists", "tables", "views",
    "schema", "indexes", "rename", "index_create", "index_drop",
    "rows", "one", "row", "col", "cols", "count", "rowcount", "lastid",
    "begin", "commit", "rollback", "savepoint", "release", "rollback_to",
    "pragma", "vacuum", "backup", "restore",
)

# Async methods — generate:  (await __ns__["db"].call("method", args...))
_ASYNC_METHODS = (
    "async_connect", "async_close",
    "async_query", "async_exec",
    "async_insert", "async_insertmany",
    "async_get", "async_getall",
    "async_begin", "async_commit", "async_rollback",
    "async_one", "async_rows", "async_count",
)


# ─────────────────────────────────────────────────────────────
# REGISTRATION
# ─────────────────────────────────────────────────────────────

def register(api):
    # Register 'db' as a lib namespace — no Python import at file level needed.
    api.lib("db", None)

    # Sync lib_call handlers → __ns__["db"].call("method", args...)
    def _make_sync_handler(method_name: str):
        def handler(args: list) -> str:
            if args:
                return f'__ns__["db"].call("{method_name}", {", ".join(args)})'
            return f'__ns__["db"].call("{method_name}")'
        return handler

    # Async lib_call handlers → (await __ns__["db"].call("method", args...))
    # call() returns a coroutine from the registered async def; awaiting it works.
    def _make_async_handler(method_name: str):
        def handler(args: list) -> str:
            if args:
                return f'(await __ns__["db"].call("{method_name}", {", ".join(args)}))'
            return f'(await __ns__["db"].call("{method_name}"))'
        return handler

    for m in _SYNC_METHODS:
        api.lib_call("db", m, _make_sync_handler(m))

    for m in _ASYNC_METHODS:
        api.lib_call("db", m, _make_async_handler(m))

    # One _DB instance per mod session
    db = _DB()

    # Register namespace dispatch table
    ns = api.namespace("db")
    for m in _SYNC_METHODS:
        ns.register(m, getattr(db, m))
    for m in _ASYNC_METHODS:
        ns.register(m, getattr(db, m))

    # Auto-close both sync and async connections after each script
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
