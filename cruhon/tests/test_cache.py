"""
Tests for the transpile cache (cruhon/core/cache.py).
"""
import marshal
import os
import tempfile
from pathlib import Path

import pytest

from cruhon.core import cache as _cache


# ── Helpers ──────────────────────────────────────────────────────────────────

def _tmp_dir(tmp_path: Path) -> tuple[Path, Path]:
    """Return (source_path, cache_dir) inside tmp_path."""
    src = tmp_path / "prog.clpy"
    src.write_text("@print[hello]", encoding="utf-8")
    cache_dir = tmp_path / ".cruhon_cache"
    return src, cache_dir


def _key(source: str = "@print[hello]", base_dir: Path = None,
         version: str = "2.7.0", mods: str = "") -> str:
    return _cache.build_key(source, base_dir or Path("."), version, mods)


def _make_code(code: str = "x = 1") -> object:
    return compile(code, "<test>", "exec")


# ── build_key ────────────────────────────────────────────────────────────────

class TestBuildKey:
    def test_deterministic(self, tmp_path):
        k1 = _key(base_dir=tmp_path)
        k2 = _key(base_dir=tmp_path)
        assert k1 == k2

    def test_source_change_invalidates(self, tmp_path):
        k1 = _key("@print[hello]", tmp_path)
        k2 = _key("@print[bye]", tmp_path)
        assert k1 != k2

    def test_version_change_invalidates(self, tmp_path):
        k1 = _key(version="2.7.0", base_dir=tmp_path)
        k2 = _key(version="2.8.0", base_dir=tmp_path)
        assert k1 != k2

    def test_mod_change_invalidates(self, tmp_path):
        k1 = _key(mods="pluginA:1.0", base_dir=tmp_path)
        k2 = _key(mods="pluginA:1.1", base_dir=tmp_path)
        assert k1 != k2

    def test_dep_change_invalidates(self, tmp_path):
        dep = tmp_path / "utils.clpy"
        dep.write_text("@var[x; 1]", encoding="utf-8")
        source_with_include = '@include["utils.clpy"]'

        k1 = _key(source_with_include, tmp_path)
        dep.write_text("@var[x; 99]", encoding="utf-8")
        k2 = _key(source_with_include, tmp_path)

        assert k1 != k2

    def test_returns_hex_string(self, tmp_path):
        k = _key(base_dir=tmp_path)
        assert len(k) == 64
        assert all(c in "0123456789abcdef" for c in k)


# ── save + try_load ───────────────────────────────────────────────────────────

class TestSaveLoad:
    def test_round_trip(self, tmp_path):
        src, cache_dir = _tmp_dir(tmp_path)
        key = _key(base_dir=tmp_path)
        python_code = "x = 42\nprint(x)"

        _cache.save(src, key, python_code, "prog.clpy", cache_dir)
        code_obj = _cache.try_load(src, key, cache_dir)

        assert code_obj is not None
        g = {}
        exec(code_obj, g)
        assert g.get("x") == 42

    def test_cache_file_is_binary(self, tmp_path):
        src, cache_dir = _tmp_dir(tmp_path)
        key = _key(base_dir=tmp_path)
        _cache.save(src, key, "x = 1", "prog.clpy", cache_dir)

        cp = cache_dir / "prog.clpy.cache"
        data = cp.read_bytes()
        assert data[:6] == b"CRUHON"
        # Must NOT contain readable Python source
        assert b"x = 1" not in data

    def test_miss_on_wrong_key(self, tmp_path):
        src, cache_dir = _tmp_dir(tmp_path)
        key1 = _key("@print[a]", tmp_path)
        key2 = _key("@print[b]", tmp_path)

        _cache.save(src, key1, "print('a')", "prog.clpy", cache_dir)
        result = _cache.try_load(src, key2, cache_dir)
        assert result is None

    def test_miss_when_no_file(self, tmp_path):
        src, cache_dir = _tmp_dir(tmp_path)
        result = _cache.try_load(src, _key(base_dir=tmp_path), cache_dir)
        assert result is None

    def test_corrupted_cache_returns_none(self, tmp_path):
        src, cache_dir = _tmp_dir(tmp_path)
        key = _key(base_dir=tmp_path)

        cache_dir.mkdir(parents=True, exist_ok=True)
        cp = cache_dir / "prog.clpy.cache"
        cp.write_bytes(b"NOT_A_VALID_CACHE_FILE")

        result = _cache.try_load(src, key, cache_dir)
        assert result is None
        assert not cp.exists()  # corrupted file deleted

    def test_atomic_write_no_partial_file(self, tmp_path):
        src, cache_dir = _tmp_dir(tmp_path)
        key = _key(base_dir=tmp_path)
        _cache.save(src, key, "x = 1", "prog.clpy", cache_dir)

        # No temp files should remain
        tmp_files = list(cache_dir.glob(".cruhon_tmp_*"))
        assert tmp_files == []

    def test_mirrors_directory_structure(self, tmp_path):
        models = tmp_path / "models"
        models.mkdir()
        src = models / "user.clpy"
        src.write_text("@var[x; 1]", encoding="utf-8")
        cache_dir = tmp_path / ".cruhon_cache"
        key = _key(base_dir=models)

        _cache.save(src, key, "x = 1", "user.clpy", cache_dir)

        expected = cache_dir / "models" / "user.clpy.cache"
        assert expected.exists()


# ── clear + stats ─────────────────────────────────────────────────────────────

class TestManagement:
    def test_clear_deletes_all(self, tmp_path):
        src, cache_dir = _tmp_dir(tmp_path)
        key = _key(base_dir=tmp_path)
        _cache.save(src, key, "x = 1", "prog.clpy", cache_dir)

        n = _cache.clear(cache_dir)
        assert n == 1
        assert list(cache_dir.rglob("*.cache")) == []

    def test_clear_empty_dir(self, tmp_path):
        cache_dir = tmp_path / ".cruhon_cache"
        n = _cache.clear(cache_dir)
        assert n == 0

    def test_stats_reports_files(self, tmp_path):
        src, cache_dir = _tmp_dir(tmp_path)
        key = _key(base_dir=tmp_path)
        _cache.save(src, key, "x = 1", "prog.clpy", cache_dir)

        s = _cache.stats(cache_dir)
        assert s["files"] == 1
        assert s["bytes"] > 0

    def test_stats_empty(self, tmp_path):
        cache_dir = tmp_path / ".cruhon_cache"
        s = _cache.stats(cache_dir)
        assert s["files"] == 0
        assert s["bytes"] == 0


# ── Integration: run_file uses cache ─────────────────────────────────────────

class TestRunFileIntegration:
    def test_cache_created_after_run(self, tmp_path):
        from cruhon.core.runner import run_file
        src = tmp_path / "hello.clpy"
        src.write_text("@var[x; 42]", encoding="utf-8")

        run_file(src)

        cache_dir = tmp_path / ".cruhon_cache"
        assert cache_dir.exists()
        assert any(cache_dir.rglob("*.cache"))

    def test_second_run_uses_cache(self, tmp_path):
        from cruhon.core.runner import run_file
        src = tmp_path / "hello.clpy"
        src.write_text("@print[hello]", encoding="utf-8")

        run_file(src)    # first run — populates cache
        run_file(src)    # second run — should hit cache (no errors = success)

    def test_no_cache_bypasses(self, tmp_path):
        from cruhon.core.runner import run_file
        src = tmp_path / "hello.clpy"
        src.write_text("@var[x; 1]", encoding="utf-8")

        run_file(src)                       # populates cache
        run_file(src, no_cache=True)        # bypasses cache
        cache_dir = tmp_path / ".cruhon_cache"
        # Cache was NOT updated by the no_cache run — original file still valid
        assert any(cache_dir.rglob("*.cache"))
