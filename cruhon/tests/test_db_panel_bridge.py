"""
Tests for the @db.attach_panel[] / @db.detach_panel[] bridge — every SQL
query on a connection is streamed live to a running cruhon-panel dashboard.
"""
import json
import sys
import threading
import time
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core import mod_loader
from cruhon.core.namespace_runtime import get_namespace_registry
from cruhon.core.runner import run_source


@pytest.fixture(scope="module", autouse=True)
def _load_mods():
    mod_loader.load_mod_from_path(Path(__file__).parent.parent.parent / "mods" / "cruhon-db")
    mod_loader.load_mod_from_path(Path(__file__).parent.parent.parent / "mods" / "cruhon-panel")


def _db():
    return get_namespace_registry().get("db")


def _panel():
    return get_namespace_registry().get("panel")


def _read_sse(url, stop_after, results, ready):
    try:
        resp = urllib.request.urlopen(url, timeout=5)
        ready.set()
        deadline = time.time() + 4
        while time.time() < deadline and len(results) < stop_after:
            line = resp.readline()
            if not line:
                break
            if line.startswith(b"data:"):
                try:
                    results.append(json.loads(line[5:].strip()))
                except Exception:
                    pass
    except Exception:
        ready.set()


class TestAttachPanelErrors:
    def test_attach_without_panel_running_raises(self):
        db = _db()
        db.call("connect", "sqlite:///:memory:")
        try:
            with pytest.raises(RuntimeError, match="not running"):
                db.call("attach_panel")
        finally:
            db.call("close")

    def test_detach_is_always_safe(self):
        db = _db()
        db.call("connect", "sqlite:///:memory:")
        try:
            db.call("detach_panel")  # no-op, never raises even if unattached
        finally:
            db.call("close")


class TestAttachPanelStreaming:
    def test_queries_stream_to_panel(self):
        db, panel = _db(), _panel()
        panel.call("start", 0)
        try:
            db.call("connect", "sqlite:///:memory:")
            db.call("attach_panel")

            url = panel.call("url") + "/stream"
            results, ready = [], threading.Event()
            t = threading.Thread(target=_read_sse, args=(url, 3, results, ready), daemon=True)
            t.start()
            assert ready.wait(timeout=3)
            time.sleep(0.2)

            db.call("exec", "CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
            db.call("insert", "t", {"name": "alice"})
            db.call("query", "SELECT * FROM t")

            t.join(timeout=5)
            events = [r for r in results if r.get("kind") == "event" and r.get("type") == "db"]
            assert len(events) >= 3
            sqls = [e["data"]["sql"] for e in events]
            assert any("CREATE TABLE" in s for s in sqls)
            assert any("INSERT INTO" in s for s in sqls)
            assert any("SELECT * FROM t" in s for s in sqls)
            assert all(e["data"]["backend"] == "sqlite" for e in events)
        finally:
            db.call("close")
            panel.call("stop")

    def test_detach_stops_streaming(self):
        # The pre-detach CREATE TABLE event is expected to appear via the
        # panel's history replay to a fresh subscriber (see test_panel.py's
        # test_history_replayed_to_new_client) — that's correct, unrelated
        # behavior. What this test actually verifies is that the INSERT
        # issued AFTER detach_panel never streams, live or in history.
        db, panel = _db(), _panel()
        panel.call("start", 0)
        try:
            db.call("connect", "sqlite:///:memory:")
            db.call("attach_panel")
            db.call("exec", "CREATE TABLE t (id INTEGER)")
            db.call("detach_panel")

            url = panel.call("url") + "/stream"
            results, ready = [], threading.Event()
            t = threading.Thread(target=_read_sse, args=(url, 1, results, ready), daemon=True)
            t.start()
            assert ready.wait(timeout=3)
            time.sleep(0.2)
            db.call("insert", "t", {"id": 1})
            time.sleep(0.3)  # give it a chance to arrive if (incorrectly) still attached
            db_events = [r for r in results if r.get("kind") == "event" and r.get("type") == "db"]
            sqls = [e["data"]["sql"] for e in db_events]
            assert not any("INSERT INTO" in s for s in sqls)
        finally:
            db.call("close")
            panel.call("stop")

    def test_broken_panel_never_breaks_queries(self):
        """Stopping the panel mid-flight must not raise from the db side."""
        db, panel = _db(), _panel()
        panel.call("start", 0)
        db.call("connect", "sqlite:///:memory:")
        db.call("attach_panel")
        panel.call("stop")  # yank the rug out
        try:
            db.call("exec", "CREATE TABLE t (id INTEGER)")  # must not raise
            db.call("insert", "t", {"id": 1})
        finally:
            db.call("close")


class TestAttachPanelCompiles:
    def test_commands_compile(self):
        from cruhon.core.transpiler import transpile
        from cruhon.core.parser import parse
        for src in ['@db.attach_panel[]', '@db.detach_panel[]']:
            compile(transpile(parse(src)), "<t>", "exec")
