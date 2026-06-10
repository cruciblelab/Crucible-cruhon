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
            f"(scope TEXT, k TEXT, v TEXT, exp REAL, PRIMARY KEY(scope, k))"
        )
        # Eski tabloları (exp sütunsuz) göçür
        try:
            self._conn.execute(f"ALTER TABLE {self._table} ADD COLUMN exp REAL")
        except Exception:
            pass
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
    def put(self, scope, k, v, exp=None):
        import json
        c = self._c()
        c.execute(f"DELETE FROM {self._table} WHERE scope=? AND k=?", (scope, str(k)))
        c.execute(f"INSERT INTO {self._table}(scope, k, v, exp) VALUES(?,?,?,?)",
                  (scope, str(k), json.dumps(v), exp))
        c.commit()
        return v

    def get(self, scope, k, default=None):
        import json, time
        cur = self._c().execute(
            f"SELECT v, exp FROM {self._table} WHERE scope=? AND k=?", (scope, str(k)))
        row = cur.fetchone()
        if not row:
            return default
        v, exp = row
        if exp is not None and time.time() > exp:
            self.delete(scope, k)
            return default
        return json.loads(v)

    # ── TTL / EXPIRE ─────────────────────────────────────────
    def setex(self, scope, k, v, seconds):
        import time
        return self.put(scope, k, v, exp=time.time() + float(seconds))

    def expire(self, scope, k, seconds):
        import time
        v = self.get(scope, k)
        if v is None and not self.has(scope, k):
            return False
        self.put(scope, k, v, exp=time.time() + float(seconds))
        return True

    def persist(self, scope, k):
        v = self.get(scope, k)
        self.put(scope, k, v, exp=None)
        return True

    def ttl(self, scope, k):
        import time
        cur = self._c().execute(
            f"SELECT exp FROM {self._table} WHERE scope=? AND k=?", (scope, str(k)))
        row = cur.fetchone()
        if not row:
            return -2          # anahtar yok
        if row[0] is None:
            return -1          # süresiz
        return max(0, int(row[0] - time.time()))

    # ── LIST (Redis-vari) ────────────────────────────────────
    def _as_list(self, scope, k):
        v = self.get(scope, k, [])
        return v if isinstance(v, list) else []

    def lpush(self, scope, k, val):
        lst = self._as_list(scope, k); lst.insert(0, val)
        self.put(scope, k, lst); return len(lst)

    def rpush(self, scope, k, val):
        lst = self._as_list(scope, k); lst.append(val)
        self.put(scope, k, lst); return len(lst)

    def lpop(self, scope, k):
        lst = self._as_list(scope, k)
        if not lst: return None
        val = lst.pop(0); self.put(scope, k, lst); return val

    def rpop(self, scope, k):
        lst = self._as_list(scope, k)
        if not lst: return None
        val = lst.pop(); self.put(scope, k, lst); return val

    def lrange(self, scope, k, start=0, end=-1):
        lst = self._as_list(scope, k)
        if end == -1:
            return lst[start:]
        return lst[start:end + 1]

    def llen(self, scope, k):
        return len(self._as_list(scope, k))

    # ── SET (benzersiz üyeler) ───────────────────────────────
    def sadd(self, scope, k, val):
        s = self._as_list(scope, k)
        if val not in s:
            s.append(val); self.put(scope, k, s); return 1
        return 0

    def srem(self, scope, k, val):
        s = self._as_list(scope, k)
        if val in s:
            s.remove(val); self.put(scope, k, s); return 1
        return 0

    def smembers(self, scope, k):
        return self._as_list(scope, k)

    def sismember(self, scope, k, val):
        return val in self._as_list(scope, k)

    def scard(self, scope, k):
        return len(self._as_list(scope, k))

    # ── HASH (alan-bazlı, Redis-vari) ────────────────────────
    def _as_dict(self, scope, k):
        v = self.get(scope, k, {})
        return v if isinstance(v, dict) else {}

    def hset(self, scope, k, field, val):
        d = self._as_dict(scope, k); d[str(field)] = val
        self.put(scope, k, d); return d

    def hget(self, scope, k, field, default=None):
        return self._as_dict(scope, k).get(str(field), default)

    def hgetall(self, scope, k):
        return self._as_dict(scope, k)

    def hdel(self, scope, k, field):
        d = self._as_dict(scope, k)
        if str(field) in d:
            del d[str(field)]; self.put(scope, k, d); return 1
        return 0

    def hkeys(self, scope, k):
        return list(self._as_dict(scope, k).keys())

    def hincr(self, scope, k, field, amount=1):
        d = self._as_dict(scope, k)
        d[str(field)] = (d.get(str(field), 0) or 0) + amount
        self.put(scope, k, d); return d[str(field)]

    # ── ATOMİK ───────────────────────────────────────────────
    def setnx(self, scope, k, v):
        """Sadece anahtar yoksa yaz (set-if-not-exists)."""
        if self.has(scope, k):
            return False
        self.put(scope, k, v); return True

    def getset(self, scope, k, v):
        """Eski değeri döndür, yenisini yaz (atomik takas)."""
        old = self.get(scope, k); self.put(scope, k, v); return old

    # ── LEADERBOARD (sayısal değere göre sıralı top N) ───────
    def leaderboard(self, scope, n=10, desc=True):
        items = self.items(scope)
        nums = [(k, v) for k, v in items.items() if isinstance(v, (int, float))]
        nums.sort(key=lambda kv: kv[1], reverse=desc)
        return nums[: int(n)] if n else nums

    def rank(self, scope, k, desc=True):
        """Bir anahtarın leaderboard'daki sırası (1-tabanlı) veya 0."""
        board = self.leaderboard(scope, 0, desc)
        for i, (key, _v) in enumerate(board, 1):
            if key == str(k):
                return i
        return 0

    # ── BACKUP / RESTORE (JSON dosya) ────────────────────────
    def backup(self, path):
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.export_all(), f, ensure_ascii=False, indent=2)
        return path

    def restore(self, path):
        import json
        with open(path, encoding="utf-8") as f:
            self.import_all(json.load(f))
        return True

    # ── DISCORD OTO-CONTEXT ──────────────────────────────────
    @staticmethod
    def _ctx_gid(ctx):
        return getattr(getattr(ctx, "guild", None), "id", 0)

    @staticmethod
    def _ctx_uid(ctx):
        u = getattr(ctx, "author", None) or getattr(ctx, "user", None)
        return getattr(u, "id", 0)

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

    # ── TTL / EXPIRE (global scope) ──────────────────────────
    h["setex"]   = lambda a: f"{_D}.setex('global', {a[0]}, {a[1]}, {a[2] if len(a)>2 else '60'})"
    h["expire"]  = lambda a: f"{_D}.expire('global', {a[0]}, {a[1] if len(a)>1 else '60'})"
    h["persist"] = lambda a: f"{_D}.persist('global', {a[0] if a else _Q})"
    h["ttl"]     = lambda a: f"{_D}.ttl('global', {a[0] if a else _Q})"

    # ── LIST (Redis-vari, global scope) ──────────────────────
    h["lpush"]   = lambda a: f"{_D}.lpush('global', {a[0]}, {a[1] if len(a)>1 else 'None'})"
    h["rpush"]   = lambda a: f"{_D}.rpush('global', {a[0]}, {a[1] if len(a)>1 else 'None'})"
    h["lpop"]    = lambda a: f"{_D}.lpop('global', {a[0] if a else _Q})"
    h["rpop"]    = lambda a: f"{_D}.rpop('global', {a[0] if a else _Q})"
    h["lrange"]  = lambda a: f"{_D}.lrange('global', {a[0]}, {a[1] if len(a)>1 else '0'}, {a[2] if len(a)>2 else '-1'})"
    h["llen"]    = lambda a: f"{_D}.llen('global', {a[0] if a else _Q})"

    # ── SET (benzersiz, global scope) ────────────────────────
    h["sadd"]      = lambda a: f"{_D}.sadd('global', {a[0]}, {a[1] if len(a)>1 else 'None'})"
    h["srem"]      = lambda a: f"{_D}.srem('global', {a[0]}, {a[1] if len(a)>1 else 'None'})"
    h["smembers"]  = lambda a: f"{_D}.smembers('global', {a[0] if a else _Q})"
    h["sismember"] = lambda a: f"{_D}.sismember('global', {a[0]}, {a[1] if len(a)>1 else 'None'})"
    h["scard"]     = lambda a: f"{_D}.scard('global', {a[0] if a else _Q})"

    # ── DISCORD OTO-CONTEXT (ctx/interaction'dan id otomatik) ─
    # @data.cset[ctx; "key"; value]  → o sunucuya yaz
    h["cset"]  = lambda a: f"{_D}.put({_D}._g({_D}._ctx_gid({a[0]})), {a[1]}, {a[2] if len(a)>2 else 'None'})"
    h["cget"]  = lambda a: f"{_D}.get({_D}._g({_D}._ctx_gid({a[0]})), {a[1]}, {a[2] if len(a)>2 else 'None'})"
    # @data.cuset[ctx; "key"; value] → o kullanıcıya yaz
    h["cuset"] = lambda a: f"{_D}.put({_D}._u({_D}._ctx_uid({a[0]})), {a[1]}, {a[2] if len(a)>2 else 'None'})"
    h["cuget"] = lambda a: f"{_D}.get({_D}._u({_D}._ctx_uid({a[0]})), {a[1]}, {a[2] if len(a)>2 else 'None'})"
    # @data.cmset[ctx; "key"; value] → o üyeye (sunucu+kullanıcı) yaz
    h["cmset"] = lambda a: f"{_D}.put({_D}._m({_D}._ctx_gid({a[0]}), {_D}._ctx_uid({a[0]})), {a[1]}, {a[2] if len(a)>2 else 'None'})"
    h["cmget"] = lambda a: f"{_D}.get({_D}._m({_D}._ctx_gid({a[0]}), {_D}._ctx_uid({a[0]})), {a[1]}, {a[2] if len(a)>2 else 'None'})"

    # ── HASH (alan-bazlı, global scope) ──────────────────────
    h["hset"]    = lambda a: f"{_D}.hset('global', {a[0]}, {a[1]}, {a[2] if len(a)>2 else 'None'})"
    h["hget"]    = lambda a: f"{_D}.hget('global', {a[0]}, {a[1]}, {a[2] if len(a)>2 else 'None'})"
    h["hgetall"] = lambda a: f"{_D}.hgetall('global', {a[0] if a else _Q})"
    h["hdel"]    = lambda a: f"{_D}.hdel('global', {a[0]}, {a[1] if len(a)>1 else _Q})"
    h["hkeys"]   = lambda a: f"{_D}.hkeys('global', {a[0] if a else _Q})"
    h["hincr"]   = lambda a: f"{_D}.hincr('global', {a[0]}, {a[1]}, {a[2] if len(a)>2 else '1'})"

    # ── ATOMİK ───────────────────────────────────────────────
    h["setnx"]   = lambda a: f"{_D}.setnx('global', {a[0]}, {a[1] if len(a)>1 else 'None'})"
    h["getset"]  = lambda a: f"{_D}.getset('global', {a[0]}, {a[1] if len(a)>1 else 'None'})"

    # ── LEADERBOARD (XP/level botları için) ──────────────────
    # @data.leaderboard[10]                → global top 10
    h["leaderboard"]  = lambda a: f"{_D}.leaderboard('global', {a[0] if a else '10'})"
    # @data.gleaderboard[guild_id; 10]     → o sunucunun top 10'u
    h["gleaderboard"] = lambda a: f"{_D}.leaderboard({_D}._g({a[0] if a else '0'}), {a[1] if len(a)>1 else '10'})"
    h["grank"]        = lambda a: f"{_D}.rank({_D}._g({a[0]}), {a[1] if len(a)>1 else '0'})"

    # ── BACKUP / RESTORE ─────────────────────────────────────
    h["backup"]  = lambda a: f"{_D}.backup({a[0] if a else repr('cruhon_data_backup.json')})"
    h["restore"] = lambda a: f"{_D}.restore({a[0] if a else repr('cruhon_data_backup.json')})"

    return h


# ─────────────────────────────────────────────────────────────
# PLUGIN ENTRY POINT
# ─────────────────────────────────────────────────────────────

def register(api):
    api.lib("data", None)  # builtin namespace — no @import needed
    api.inject("__cruhon_data__", _CruhonData())
    for method, handler in _build().items():
        api.lib_call("data", method, handler)
