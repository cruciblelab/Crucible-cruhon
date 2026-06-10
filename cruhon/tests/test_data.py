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
