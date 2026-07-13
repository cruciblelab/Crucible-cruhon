"""
Regression test for a severe bug in cruhon-shortcuts (a prominently
recommended, headline plugin per the README): its "data" group
registered @store.all/@store.keys/@store.values/@store.has using
cruhon.core.libs.store_._STORE — an attribute that has never existed.
@store.* is backed by a JSON file (.cruhon_store.json), read/written via
the __cruhon_store_* helpers the transpiler injects, not an in-memory
dict named _STORE.

Impact: any real user who loaded cruhon-shortcuts (as the README's own
"Shortcut Plugins" section recommends) had @store.all/keys/values/has
COMPLETELY BROKEN — every call raised AttributeError: module
'cruhon.core.libs.store_' has no attribute '_STORE'. Additionally,
@store.all was needlessly re-registered here, overwriting (and breaking)
the already-correct core handler for anyone with this plugin loaded.

Found via the full test suite: a different, unrelated test elsewhere in
the session loaded cruhon-shortcuts (a real, global, process-wide
registry mutation via api.lib_call), which then broke a completely
unrelated @store test running later in the same pytest process — a
sharp reminder that mod registrations are global state, not scoped to
the test that loads them.
"""
import io
import contextlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core import mod_loader
from cruhon.core.runner import run_source


@pytest.fixture(scope="module", autouse=True)
def _load_shortcuts_mod():
    mod_path = Path(__file__).parent.parent.parent / "mods" / "cruhon-shortcuts"
    mod_loader.load_mod_from_path(mod_path)


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def run(src):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_source(src)
    return buf.getvalue()


class TestStoreWithShortcutsLoaded:
    def test_all_still_works(self):
        out = run('@store.set["x"; 1]\n@var[a; @store.all]\n@print[{a}]')
        assert "{'x': 1}" in out

    def test_keys_works(self):
        out = run('@store.set["a"; 1]\n@store.set["b"; 2]\n@var[k; @store.keys]\n@print[{k}]')
        assert out.strip() == "['a', 'b']"

    def test_values_works(self):
        out = run('@store.set["a"; 1]\n@store.set["b"; 2]\n@var[v; @store.values]\n@print[{v}]')
        assert out.strip() == "[1, 2]"

    def test_has_true(self):
        out = run('@store.set["x"; 1]\n@var[h; @store.has["x"]]\n@print[{h}]')
        assert out.strip() == "True"

    def test_has_false(self):
        out = run('@var[h; @store.has["nope"]]\n@print[{h}]')
        assert out.strip() == "False"

    def test_clear_still_works(self):
        out = run(
            '@store.set["x"; 1]\n'
            '@store.clear[]\n'
            '@var[a; @store.all]\n'
            '@print[{a}]'
        )
        assert out.strip() == "{}"
