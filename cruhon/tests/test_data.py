"""
Test suite for the cruhon-data plugin (@data.* scoped key-value store).

Two layers:
  - Runtime: exercise the injected _CruhonData store directly (:memory:).
  - Transpile: load the plugin and check @data.X[...] emits correct Python.
"""
import sys
import importlib.util
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core import mod_loader
from cruhon.core.parser import parse
from cruhon.core.transpiler import transpile


# ── load the runtime class directly ───────────────────────────
_spec = importlib.util.spec_from_file_location(
    "_cruhon_data_mod",
    Path(__file__).parent.parent.parent / "mods" / "cruhon-data" / "__init__.py",
)
_data_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_data_mod)
CruhonData = _data_mod._CruhonData


@pytest.fixture(scope="module", autouse=True)
def _load_data_mod():
    mod_path = Path(__file__).parent.parent.parent / "mods" / "cruhon-data"
    mod_loader.load_mod_from_path(mod_path)


def _compile(source: str) -> str:
    code = transpile(parse(source))
    indented = "\n".join("    " + line for line in code.splitlines())
    wrapper = "def __c__():\n" + (indented if indented.strip() else "    pass")
    compile(wrapper, "<test>", "exec")
    return code


# ─────────────────────────────────────────────────────────────
# RUNTIME — gerçek davranış
# ─────────────────────────────────────────────────────────────

class TestDataRuntime:
    def _store(self):
        return CruhonData().open(":memory:")

    def test_global_set_get(self):
        d = self._store()
        d.put("global", "prefix", "!")
        assert d.get("global", "prefix") == "!"

    def test_get_default(self):
        d = self._store()
        assert d.get("global", "yok", "varsayilan") == "varsayilan"

    def test_json_values(self):
        d = self._store()
        d.put("global", "cfg", {"a": 1, "b": [1, 2, 3]})
        assert d.get("global", "cfg") == {"a": 1, "b": [1, 2, 3]}

    def test_guild_scope_isolation(self):
        d = self._store()
        d.put(d._g(111), "welcome", "Merhaba A")
        d.put(d._g(222), "welcome", "Merhaba B")
        assert d.get(d._g(111), "welcome") == "Merhaba A"
        assert d.get(d._g(222), "welcome") == "Merhaba B"

    def test_user_and_member_scope(self):
        d = self._store()
        d.put(d._u(7), "xp", 50)
        d.put(d._m(111, 7), "xp", 99)
        assert d.get(d._u(7), "xp") == 50
        assert d.get(d._m(111, 7), "xp") == 99

    def test_incr_counter(self):
        d = self._store()
        assert d.incr("global", "count") == 1
        assert d.incr("global", "count", 5) == 6

    def test_has_and_delete(self):
        d = self._store()
        d.put("global", "k", 1)
        assert d.has("global", "k") is True
        d.delete("global", "k")
        assert d.has("global", "k") is False

    def test_keys_and_items(self):
        d = self._store()
        d.put(d._g(1), "a", 1)
        d.put(d._g(1), "b", 2)
        assert set(d.keys(d._g(1))) == {"a", "b"}
        assert d.items(d._g(1)) == {"a": 1, "b": 2}

    def test_export_import_sync(self):
        d = self._store()
        d.put("global", "x", 1)
        d.put(d._g(5), "y", 2)
        dump = d.export_all()
        # yeni store'a aktar (başka DB'ye senkron simülasyonu)
        d2 = self._store()
        d2.import_all(dump)
        assert d2.get("global", "x") == 1
        assert d2.get(d2._g(5), "y") == 2

    def test_clear_scope(self):
        d = self._store()
        d.put(d._g(1), "a", 1)
        d.put(d._g(2), "b", 2)
        d.clear_scope(d._g(1))
        assert d.items(d._g(1)) == {}
        assert d.get(d._g(2), "b") == 2

    def test_attach_external_connection(self):
        import sqlite3
        conn = sqlite3.connect(":memory:")
        d = CruhonData().attach(conn)
        d.put("global", "k", "v")
        assert d.get("global", "k") == "v"
        # aynı bağlantı ham erişilebilir
        assert d.connection() is conn


# ─────────────────────────────────────────────────────────────
# TRANSPILE — emit doğruluğu
# ─────────────────────────────────────────────────────────────

class TestDataTranspile:
    def test_global_set_get(self):
        assert "__cruhon_data__.put('global', \"prefix\", \"!\")" in _compile('@data.set["prefix"; "!"]')
        assert "__cruhon_data__.get('global', \"prefix\", None)" in _compile('@var[p; @data.get["prefix"]]')

    def test_get_with_default(self):
        assert "__cruhon_data__.get('global', \"k\", 0)" in _compile('@var[v; @data.get["k"; 0]]')

    def test_guild_scoped(self):
        code = _compile('@data.gset[guild.id; "welcome"; "Selam"]')
        assert "__cruhon_data__.put(__cruhon_data__._g(guild.id), \"welcome\", \"Selam\")" in code

    def test_guild_get(self):
        code = _compile('@var[w; @data.gget[gid; "welcome"; "yok"]]')
        assert "__cruhon_data__.get(__cruhon_data__._g(gid), \"welcome\", \"yok\")" in code

    def test_user_scoped(self):
        code = _compile('@data.uset[user.id; "xp"; 100]')
        assert "__cruhon_data__.put(__cruhon_data__._u(user.id), \"xp\", 100)" in code

    def test_member_scoped(self):
        code = _compile('@data.mset[gid; uid; "level"; 5]')
        assert "__cruhon_data__.put(__cruhon_data__._m(gid, uid), \"level\", 5)" in code

    def test_incr(self):
        assert "__cruhon_data__.incr('global', \"hits\", 1)" in _compile('@data.incr["hits"]')
        assert "__cruhon_data__.gincr(" not in _compile('@data.incr["hits"]')

    def test_open_default(self):
        assert "__cruhon_data__.open('cruhon_data.db')" in _compile("@data.open[]")

    def test_export(self):
        assert "__cruhon_data__.export_all()" in _compile("@var[d; @data.export[]]")

    def test_connection_raw(self):
        assert "__cruhon_data__.connection()" in _compile("@var[c; @data.connection[]]")


# ─────────────────────────────────────────────────────────────
# GENİŞLETME — TTL / LIST / SET / OTO-CONTEXT
# ─────────────────────────────────────────────────────────────

class TestDataTTL:
    def _s(self):
        return CruhonData().open(":memory:")

    def test_setex_and_ttl(self):
        d = self._s()
        d.setex("global", "tok", "abc", 100)
        assert d.get("global", "tok") == "abc"
        assert 0 < d.ttl("global", "tok") <= 100

    def test_expired_returns_default(self):
        d = self._s()
        d.setex("global", "tok", "abc", -1)  # zaten süresi geçmiş
        assert d.get("global", "tok", "yok") == "yok"

    def test_persist_removes_expiry(self):
        d = self._s()
        d.setex("global", "k", 1, 100)
        d.persist("global", "k")
        assert d.ttl("global", "k") == -1

    def test_ttl_missing(self):
        assert self._s().ttl("global", "yok") == -2


class TestDataList:
    def _s(self):
        return CruhonData().open(":memory:")

    def test_push_pop(self):
        d = self._s()
        d.rpush("global", "q", "a")
        d.rpush("global", "q", "b")
        d.lpush("global", "q", "x")
        assert d.lrange("global", "q", 0, -1) == ["x", "a", "b"]
        assert d.lpop("global", "q") == "x"
        assert d.rpop("global", "q") == "b"
        assert d.llen("global", "q") == 1

    def test_lrange_slice(self):
        d = self._s()
        for n in range(5):
            d.rpush("global", "l", n)
        assert d.lrange("global", "l", 1, 3) == [1, 2, 3]


class TestDataSet:
    def _s(self):
        return CruhonData().open(":memory:")

    def test_set_unique(self):
        d = self._s()
        assert d.sadd("global", "s", "a") == 1
        assert d.sadd("global", "s", "a") == 0  # zaten var
        d.sadd("global", "s", "b")
        assert set(d.smembers("global", "s")) == {"a", "b"}
        assert d.sismember("global", "s", "a") is True
        assert d.scard("global", "s") == 2
        d.srem("global", "s", "a")
        assert d.sismember("global", "s", "a") is False


class TestDataContext:
    """Discord ctx/interaction'dan otomatik id çıkarımı."""

    class _FakeGuild:
        id = 999

    class _FakeUser:
        id = 42

    class _FakeCtx:
        guild = TestDataContext._FakeGuild() if False else None  # placeholder

    def test_ctx_gid_uid(self):
        class G: id = 999
        class U: id = 42
        class Ctx:
            guild = G()
            author = U()
        d = CruhonData().open(":memory:")
        d.put(d._g(d._ctx_gid(Ctx())), "x", 1)
        assert d.get(d._g(999), "x") == 1
        d.put(d._u(d._ctx_uid(Ctx())), "y", 2)
        assert d.get(d._u(42), "y") == 2

    def test_interaction_uses_user(self):
        class U: id = 7
        class Interaction:
            user = U()
            guild = None
        d = CruhonData().open(":memory:")
        assert d._ctx_uid(Interaction()) == 7


class TestDataExtTranspile:
    def test_ttl_emit(self):
        assert "__cruhon_data__.setex('global', \"t\", \"v\", 30)" in _compile('@data.setex["t"; "v"; 30]')
        assert "__cruhon_data__.ttl('global', \"t\")" in _compile('@var[x; @data.ttl["t"]]')

    def test_list_emit(self):
        assert "__cruhon_data__.rpush('global', \"q\", item)" in _compile('@data.rpush["q"; item]')
        assert "__cruhon_data__.lrange('global', \"q\", 0, -1)" in _compile('@var[l; @data.lrange["q"]]')

    def test_set_emit(self):
        assert "__cruhon_data__.sadd('global', \"tags\", \"x\")" in _compile('@data.sadd["tags"; "x"]')

    def test_context_emit(self):
        code = _compile('@data.cset[ctx; "warns"; 3]')
        assert "__cruhon_data__.put(__cruhon_data__._g(__cruhon_data__._ctx_gid(ctx)), \"warns\", 3)" in code

    def test_context_member_emit(self):
        code = _compile('@var[w; @data.cmget[ctx; "warns"; 0]]')
        assert "_ctx_gid(ctx)" in code and "_ctx_uid(ctx)" in code


# ─────────────────────────────────────────────────────────────
# GÜÇ DALGASI — hash / leaderboard / atomik / backup
# ─────────────────────────────────────────────────────────────

class TestDataHash:
    def _s(self): return CruhonData().open(":memory:")

    def test_hash_ops(self):
        d = self._s()
        d.hset("global", "user:1", "name", "Ali")
        d.hset("global", "user:1", "age", 30)
        assert d.hget("global", "user:1", "name") == "Ali"
        assert d.hgetall("global", "user:1") == {"name": "Ali", "age": 30}
        assert set(d.hkeys("global", "user:1")) == {"name", "age"}
        d.hdel("global", "user:1", "age")
        assert d.hget("global", "user:1", "age", "yok") == "yok"

    def test_hincr(self):
        d = self._s()
        assert d.hincr("global", "stats", "wins") == 1
        assert d.hincr("global", "stats", "wins", 4) == 5


class TestDataAtomic:
    def _s(self): return CruhonData().open(":memory:")

    def test_setnx(self):
        d = self._s()
        assert d.setnx("global", "k", "ilk") is True
        assert d.setnx("global", "k", "ikinci") is False
        assert d.get("global", "k") == "ilk"

    def test_getset(self):
        d = self._s()
        d.put("global", "k", "eski")
        assert d.getset("global", "k", "yeni") == "eski"
        assert d.get("global", "k") == "yeni"


class TestDataLeaderboard:
    def _s(self): return CruhonData().open(":memory:")

    def test_leaderboard_top(self):
        d = self._s()
        for k, v in [("a", 10), ("b", 50), ("c", 30)]:
            d.put(d._g(1), k, v)
        board = d.leaderboard(d._g(1), 2)
        assert board == [("b", 50), ("c", 30)]

    def test_rank(self):
        d = self._s()
        for k, v in [("a", 10), ("b", 50), ("c", 30)]:
            d.put(d._g(1), k, v)
        assert d.rank(d._g(1), "b") == 1
        assert d.rank(d._g(1), "a") == 3
        assert d.rank(d._g(1), "yok") == 0


class TestDataBackup:
    def test_backup_restore(self, tmp_path):
        d = CruhonData().open(":memory:")
        d.put("global", "x", 1)
        d.put(d._g(9), "y", [1, 2, 3])
        path = str(tmp_path / "bak.json")
        d.backup(path)
        d2 = CruhonData().open(":memory:")
        d2.restore(path)
        assert d2.get("global", "x") == 1
        assert d2.get(d2._g(9), "y") == [1, 2, 3]


class TestDataPowerTranspile:
    def test_hash_emit(self):
        assert "__cruhon_data__.hset('global', \"u\", \"name\", \"Ali\")" in _compile('@data.hset["u"; "name"; "Ali"]')

    def test_leaderboard_emit(self):
        assert "__cruhon_data__.leaderboard(__cruhon_data__._g(gid), 5)" in _compile('@var[t; @data.gleaderboard[gid; 5]]')

    def test_setnx_emit(self):
        assert "__cruhon_data__.setnx('global', \"k\", 1)" in _compile('@data.setnx["k"; 1]')

    def test_backup_emit(self):
        assert "__cruhon_data__.backup('cruhon_data_backup.json')" in _compile("@data.backup[]")
