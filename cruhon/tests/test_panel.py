"""
Tests for the cruhon-panel plugin (@panel.*) — live log-stream dashboard.

Exercises the real HTTP server: dashboard page, SSE stream, fan-out of
logs/metrics/events, and @log.* integration.
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
from cruhon.core.runner import run_source


@pytest.fixture(scope="module", autouse=True)
def _load_panel_mod():
    mod_path = Path(__file__).parent.parent.parent / "mods" / "cruhon-panel"
    mod_loader.load_mod_from_path(mod_path)


def _ns():
    """Reach the live panel Namespace object."""
    from cruhon.core.namespace_runtime import get_namespace_registry
    return get_namespace_registry().get("panel")


def _read_sse(url, stop_after, results, ready):
    """Open an SSE stream, signal readiness, collect events until stop_after."""
    try:
        resp = urllib.request.urlopen(url, timeout=5)
        ready.set()
        deadline = time.time() + 4
        buf = b""
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


class TestPanelLifecycle:
    def test_start_stop_url(self):
        # port 0 → OS picks a free port. Drive the namespace directly:
        # run_source() fires destroy hooks at end-of-script, which would
        # stop the panel before we could inspect it.
        ns = _ns()
        url = ns.call("start", 0)
        try:
            assert url.startswith("http://")
            assert ns.call("running") is True
        finally:
            ns.call("stop")
        assert ns.call("running") is False

    def test_dashboard_served(self):
        ns = _ns()
        ns.call("start", 0)
        try:
            url = ns.call("url")
            html = urllib.request.urlopen(url, timeout=5).read().decode()
            assert "Cruhon Panel" in html
            assert "EventSource('/stream')" in html
        finally:
            ns.call("stop")

    def test_running_reflects_state(self):
        ns = _ns()
        assert ns.call("running") is False
        ns.call("start", 0)
        assert ns.call("running") is True
        ns.call("stop")
        assert ns.call("running") is False


class TestPanelStreaming:
    def test_log_reaches_browser(self):
        ns = _ns()
        ns.call("start", 0)
        url = ns.call("url") + "/stream"
        try:
            results, ready = [], threading.Event()
            t = threading.Thread(target=_read_sse, args=(url, 3, results, ready), daemon=True)
            t.start()
            assert ready.wait(timeout=3)
            time.sleep(0.2)  # let the subscriber register
            ns.call("log", "hello panel")
            ns.call("log", "a warning", "WARNING")
            ns.call("metric", "users", 42)
            t.join(timeout=5)
            kinds = [r.get("kind") for r in results]
            assert "log" in kinds
            msgs = [r.get("msg") for r in results if r.get("kind") == "log"]
            assert "hello panel" in msgs
            assert any(r.get("kind") == "metric" and r.get("value") == 42 for r in results)
        finally:
            ns.call("stop")

    def test_history_replayed_to_new_client(self):
        ns = _ns()
        ns.call("start", 0)
        try:
            # Emit before anyone connects — should sit in history.
            ns.call("log", "earlier line")
            url = ns.call("url") + "/stream"
            results, ready = [], threading.Event()
            t = threading.Thread(target=_read_sse, args=(url, 1, results, ready), daemon=True)
            t.start()
            assert ready.wait(timeout=3)
            t.join(timeout=5)
            assert any(r.get("msg") == "earlier line" for r in results)
        finally:
            ns.call("stop")

    def test_clients_count(self):
        ns = _ns()
        ns.call("start", 0)
        url = ns.call("url") + "/stream"
        try:
            assert ns.call("clients") == 0
            results, ready = [], threading.Event()
            t = threading.Thread(target=_read_sse, args=(url, 1, results, ready), daemon=True)
            t.start()
            assert ready.wait(timeout=3)
            time.sleep(0.3)
            assert ns.call("clients") >= 1
        finally:
            ns.call("stop")


class TestPanelLogging:
    def test_attach_logging_mirrors_to_panel(self):
        ns = _ns()
        ns.call("start", 0)
        url = ns.call("url") + "/stream"
        try:
            ns.call("attach_logging", "INFO")
            results, ready = [], threading.Event()
            t = threading.Thread(target=_read_sse, args=(url, 1, results, ready), daemon=True)
            t.start()
            assert ready.wait(timeout=3)
            time.sleep(0.2)
            import logging
            logging.getLogger("test.panel").info("from logging module")
            t.join(timeout=5)
            assert any("from logging module" in str(r.get("msg", "")) for r in results)
        finally:
            ns.call("detach_logging")
            ns.call("stop")


class TestPanelCompiles:
    def test_all_commands_compile(self):
        from cruhon.core.transpiler import transpile
        from cruhon.core.parser import parse
        for src in [
            '@panel.start[8787]',
            '@panel.start[8787; "0.0.0.0"]',
            '@var[u; @panel.url[]]',
            '@panel.log["hi"]',
            '@panel.log["hi"; "ERROR"]',
            '@panel.info["x"]',
            '@panel.metric["rps"; 12.5]',
            '@panel.event["deploy"; {"ok": True}]',
            '@panel.attach_logging["DEBUG"]',
            '@panel.clear[]',
            '@panel.wait[5]',
            '@panel.stop[]',
        ]:
            compile(transpile(parse(src)), "<t>", "exec")
