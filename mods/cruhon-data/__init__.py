"""
cruhon-data — fast, zero-config, scoped persistent key-value store  (@data.*)
=============================================================================
"Even people who don't know SQL can save and load anything — per server,
 per user, or globally — and still sync with any real database."

Backed by SQLite (zero-config, fast, persistent). Values are JSON-serialized
so you can store text, numbers, lists, and dicts transparently.

Scopes
------
  GLOBAL   — one value for the whole bot
  GUILD    — one value per server (guild_id)
  USER     — one value per user (user_id)
  MEMBER   — one value per (guild_id, user_id) pair

━━━ AÇ / KAPAT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @data.open[]                      — varsayılan dosya: cruhon_data.db
  @data.open["bot.db"]              — özel dosya  (":memory:" = geçici)
  @data.close[]

━━━ GLOBAL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @data.set["key"; value]
  @data.get["key"]                  → değer veya None
  @data.get["key"; default]
  @data.delete["key"]
  @data.has["key"]                  → bool
  @data.incr["key"]                 — +1 (atomik sayaç)
  @data.incr["key"; n]              — +n
  @data.keys[]                      → liste
  @data.all[]                       → dict

━━━ SUNUCU BAZLI (GUILD) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @data.gset[guild_id; "key"; value]
  @data.gget[guild_id; "key"]  /  @data.gget[guild_id; "key"; default]
  @data.gdelete[guild_id; "key"]
  @data.ghas[guild_id; "key"]       → bool
  @data.gincr[guild_id; "key"; n]
  @data.gall[guild_id]              → o sunucunun tüm verisi (dict)
  @data.gkeys[guild_id]             → liste

━━━ KULLANICI BAZLI (USER) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @data.uset[user_id; "key"; value]
  @data.uget[user_id; "key"]  /  @data.uget[user_id; "key"; default]
  @data.udelete[user_id; "key"]
  @data.uincr[user_id; "key"; n]
  @data.uall[user_id]               → dict

━━━ ÜYE BAZLI (GUILD + USER) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @data.mset[guild_id; user_id; "key"; value]
  @data.mget[guild_id; user_id; "key"]  /  ...; default]
  @data.mdelete[guild_id; user_id; "key"]
  @data.mincr[guild_id; user_id; "key"; n]

━━━ SENKRON & HAM ERİŞİM (diğer DB kütüphaneleriyle) ━━━━━━━━━━━━━━━━━━━━━━
  @data.export[]                    → tüm veriyi dict olarak ver
  @data.import[dict]                — dict'ten yükle (toplu)
  @data.attach[connection]          — mevcut bir DBAPI bağlantısını kullan
  @data.connection[]                → ham SQLite bağlantısı (tam özgürlük)
  @data.clear[]                     — her şeyi sil
  @data.clear_guild[guild_id]       — sadece o sunucuyu sil
"""
from __future__ import annotations


# ─────────────────────────────────────────────────────────────
# RUNTIME STORE — injected as __cruhon_data__
# ─────────────────────────────────────────────────────────────

class _CruhonData:
    """SQLite-backed scoped key-value store. JSON values. Portable upsert."""

    def __init__(self):
        self._conn = None
        self._table = "cruhon_data"

    # ── lifecycle ────────────────────────────────────────────
    def open(self, path="cruhon_data.db", table="cruhon_data"):
        import sqlite3
        self._conn = sqlite3.connect(path)
        self._table = table
        self._ensure()
        return self

    def attach(self, conn, table="cruhon_data"):
        """Use an existing DBAPI connection (sync with other DB libraries)."""
        self._conn = conn
        self._table = table
        self._ensure()
        return self

    def _ensure(self):
        self._conn.execute(
            f"CREATE TABLE IF NOT EXISTS {self._table} "
            f"(scope TEXT, k TEXT, v TEXT, PRIMARY KEY(scope, k))"
        )
        self._conn.commit()

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _c(self):
        if self._conn is None:
            self.open()  # lazy auto-open with default file
        return self._conn

    def connection(self):
        return self._c()

    # ── core (portable: DELETE + INSERT upsert) ──────────────
    def put(self, scope, k, v):
        import json
        c = self._c()
        c.execute(f"DELETE FROM {self._table} WHERE scope=? AND k=?", (scope, str(k)))
        c.execute(f"INSERT INTO {self._table}(scope, k, v) VALUES(?,?,?)",
                  (scope, str(k), json.dumps(v)))
        c.commit()
        return v

    def get(self, scope, k, default=None):
        import json
        cur = self._c().execute(
            f"SELECT v FROM {self._table} WHERE scope=? AND k=?", (scope, str(k)))
        row = cur.fetchone()
        return json.loads(row[0]) if row else default

    def delete(self, scope, k):
        c = self._c()
        c.execute(f"DELETE FROM {self._table} WHERE scope=? AND k=?", (scope, str(k)))
        c.commit()

    def has(self, scope, k):
        cur = self._c().execute(
            f"SELECT 1 FROM {self._table} WHERE scope=? AND k=?", (scope, str(k)))
        return cur.fetchone() is not None

    def incr(self, scope, k, amount=1):
        cur = self.get(scope, k, 0)
        try:
            cur = (cur or 0) + amount
        except TypeError:
            cur = amount
        self.put(scope, k, cur)
        return cur

    def keys(self, scope):
        cur = self._c().execute(
            f"SELECT k FROM {self._table} WHERE scope=?", (scope,))
        return [r[0] for r in cur.fetchall()]

    def items(self, scope):
        import json
        cur = self._c().execute(
            f"SELECT k, v FROM {self._table} WHERE scope=?", (scope,))
        return {r[0]: json.loads(r[1]) for r in cur.fetchall()}

    def clear_scope(self, scope):
        c = self._c()
        c.execute(f"DELETE FROM {self._table} WHERE scope=?", (scope,))
        c.commit()

    def clear_all(self):
        c = self._c()
        c.execute(f"DELETE FROM {self._table}")
        c.commit()

    # ── sync bridge ──────────────────────────────────────────
    def export_all(self):
        import json
        cur = self._c().execute(f"SELECT scope, k, v FROM {self._table}")
        out = {}
        for scope, k, v in cur.fetchall():
            out.setdefault(scope, {})[k] = json.loads(v)
        return out

    def import_all(self, data):
        for scope, kv in (data or {}).items():
            for k, v in kv.items():
                self.put(scope, k, v)
        return True

    # ── scope helpers ────────────────────────────────────────
    @staticmethod
    def _g(gid):  return f"g:{gid}"
    @staticmethod
    def _u(uid):  return f"u:{uid}"
    @staticmethod
    def _m(gid, uid): return f"m:{gid}:{uid}"


# ─────────────────────────────────────────────────────────────
# LIB CALL HANDLERS — @data.X[...]
# ─────────────────────────────────────────────────────────────

_D = "__cruhon_data__"
_Q = '""'  # empty-string literal (avoids backslash in f-strings)


def _build() -> dict:
    h = {}

    # ── lifecycle ────────────────────────────────────────────
    h["open"]   = lambda a: f"{_D}.open({a[0] if a else repr('cruhon_data.db')})"
    h["close"]  = lambda a: f"{_D}.close()"
    h["attach"] = lambda a: f"{_D}.attach({a[0] if a else 'conn'})"
    h["connection"] = lambda a: f"{_D}.connection()"
    h["clear"]  = lambda a: f"{_D}.clear_all()"
    h["clear_guild"] = lambda a: f"{_D}.clear_scope({_D}._g({a[0] if a else '0'}))"
    h["export"] = lambda a: f"{_D}.export_all()"
    h["import"] = lambda a: f"{_D}.import_all({a[0] if a else '{{}}'})"

    # ── GLOBAL ───────────────────────────────────────────────
    h["set"]    = lambda a: f"{_D}.put('global', {a[0]}, {a[1] if len(a)>1 else 'None'})"
    h["get"]    = lambda a: f"{_D}.get('global', {a[0]}, {a[1] if len(a)>1 else 'None'})"
    h["delete"] = lambda a: f"{_D}.delete('global', {a[0] if a else _Q})"
    h["has"]    = lambda a: f"{_D}.has('global', {a[0] if a else _Q})"
    h["incr"]   = lambda a: f"{_D}.incr('global', {a[0]}, {a[1] if len(a)>1 else '1'})"
    h["keys"]   = lambda a: f"{_D}.keys('global')"
    h["all"]    = lambda a: f"{_D}.items('global')"

    # ── GUILD ────────────────────────────────────────────────
    h["gset"]    = lambda a: f"{_D}.put({_D}._g({a[0]}), {a[1]}, {a[2] if len(a)>2 else 'None'})"
    h["gget"]    = lambda a: f"{_D}.get({_D}._g({a[0]}), {a[1]}, {a[2] if len(a)>2 else 'None'})"
    h["gdelete"] = lambda a: f"{_D}.delete({_D}._g({a[0]}), {a[1] if len(a)>1 else _Q})"
    h["ghas"]    = lambda a: f"{_D}.has({_D}._g({a[0]}), {a[1] if len(a)>1 else _Q})"
    h["gincr"]   = lambda a: f"{_D}.incr({_D}._g({a[0]}), {a[1]}, {a[2] if len(a)>2 else '1'})"
    h["gkeys"]   = lambda a: f"{_D}.keys({_D}._g({a[0] if a else '0'}))"
    h["gall"]    = lambda a: f"{_D}.items({_D}._g({a[0] if a else '0'}))"

    # ── USER ─────────────────────────────────────────────────
    h["uset"]    = lambda a: f"{_D}.put({_D}._u({a[0]}), {a[1]}, {a[2] if len(a)>2 else 'None'})"
    h["uget"]    = lambda a: f"{_D}.get({_D}._u({a[0]}), {a[1]}, {a[2] if len(a)>2 else 'None'})"
    h["udelete"] = lambda a: f"{_D}.delete({_D}._u({a[0]}), {a[1] if len(a)>1 else _Q})"
    h["uhas"]    = lambda a: f"{_D}.has({_D}._u({a[0]}), {a[1] if len(a)>1 else _Q})"
    h["uincr"]   = lambda a: f"{_D}.incr({_D}._u({a[0]}), {a[1]}, {a[2] if len(a)>2 else '1'})"
    h["uall"]    = lambda a: f"{_D}.items({_D}._u({a[0] if a else '0'}))"

    # ── MEMBER (guild + user) ────────────────────────────────
    h["mset"]    = lambda a: f"{_D}.put({_D}._m({a[0]}, {a[1]}), {a[2]}, {a[3] if len(a)>3 else 'None'})"
    h["mget"]    = lambda a: f"{_D}.get({_D}._m({a[0]}, {a[1]}), {a[2]}, {a[3] if len(a)>3 else 'None'})"
    h["mdelete"] = lambda a: f"{_D}.delete({_D}._m({a[0]}, {a[1]}), {a[2] if len(a)>2 else _Q})"
    h["mincr"]   = lambda a: f"{_D}.incr({_D}._m({a[0]}, {a[1]}), {a[2]}, {a[3] if len(a)>3 else '1'})"

    return h


# ─────────────────────────────────────────────────────────────
# PLUGIN ENTRY POINT
# ─────────────────────────────────────────────────────────────

def register(api):
    api.lib("data", None)  # builtin namespace — no @import needed
    api.inject("__cruhon_data__", _CruhonData())
    for method, handler in _build().items():
        api.lib_call("data", method, handler)
