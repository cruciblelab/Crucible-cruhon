"""
Tests for wave-7 method expansions:
@ftp, @pop3, @weakref, @httpserver, @argparse, @selectors
"""
import socket as _socket
import urllib.request

import pytest

from cruhon.core.transpiler import Transpiler
from cruhon.core.parser import Parser


def transpile(src):
    return Transpiler().transpile(Parser().parse(src))


def run(src, globs=None):
    g = globs or {}
    exec(compile(transpile(src), "<test>", "exec"), g)
    return g


def compiles(src):
    compile(transpile(src), "<test>", "exec")
    return True


# ─────────────────────────────────────────────────────────────
# @ftp / @pop3 — compile-only (need live servers)
# ─────────────────────────────────────────────────────────────

class TestFtpExpanded:
    def test_rename_compiles(self):
        assert compiles('@ftp.rename[f; "a.txt"; "b.txt"]')

    def test_mkdir_compiles(self):
        assert compiles('@ftp.mkdir[f; "newdir"]')

    def test_passive_compiles(self):
        assert compiles('@var[g; @ftp.passive[f; True]]')


class TestPop3Expanded:
    def test_top_compiles(self):
        assert compiles('@var[h; @pop3.top[p; 1; 5]]')

    def test_uidl_compiles(self):
        assert compiles('@var[u; @pop3.uidl[p]]')

    def test_reset_compiles(self):
        assert compiles('@pop3.reset[p]')


# ─────────────────────────────────────────────────────────────
# @weakref — finalize
# ─────────────────────────────────────────────────────────────

class _Obj:
    pass


class TestWeakrefFinalize:
    def test_finalize_runs_on_gc(self):
        import gc
        hits = []
        o = _Obj()
        run('@weakref.finalize[o; cb]', {"o": o, "cb": lambda: hits.append(1)})
        del o
        gc.collect()
        assert hits == [1]

    def test_finalize_returns_object(self):
        import weakref
        o = _Obj()
        g = run('@var[f; @weakref.finalize[o; cb]]', {"o": o, "cb": lambda: None})
        assert isinstance(g["f"], weakref.finalize)


# ─────────────────────────────────────────────────────────────
# @httpserver — threaded / serve_async
# ─────────────────────────────────────────────────────────────

class TestHttpServerExpanded:
    def test_serve_async_loopback(self, tmp_path):
        (tmp_path / "hi.txt").write_text("async cruhon")
        src = (
            f'@var[srv; @httpserver.threaded[0; "{tmp_path}"]]\n'
            f'@var[port; @httpserver.port[srv]]\n'
            f'@var[thread; @httpserver.serve_async[srv]]'
        )
        g = run(src)
        srv, port = g["srv"], g["port"]
        try:
            data = urllib.request.urlopen(f"http://127.0.0.1:{port}/hi.txt", timeout=5).read()
            assert data == b"async cruhon"
        finally:
            run('@httpserver.stop[srv]', {"srv": srv})
            run('@httpserver.close[srv]', {"srv": srv})

    def test_threaded_type(self):
        import http.server
        g = run('@var[s; @httpserver.threaded[0]]')
        assert isinstance(g["s"], http.server.ThreadingHTTPServer)
        g["s"].server_close()


# ─────────────────────────────────────────────────────────────
# @argparse — object workflow
# ─────────────────────────────────────────────────────────────

class TestArgparseExpanded:
    def test_add_and_run(self):
        src = (
            '@var[p; @argparse.new["tool"]]\n'
            '@argparse.add[p; "--name"]\n'
            '@var[ns; @argparse.run[p; ["--name", "bob"]]]'
        )
        g = run(src)
        assert g["ns"].name == "bob"

    def test_add_with_opts(self):
        src = (
            '@var[p; @argparse.new[]]\n'
            '@argparse.add[p; "--count"; {"type": int}]\n'
            '@var[ns; @argparse.run[p; ["--count", "7"]]]'
        )
        g = run(src)
        assert g["ns"].count == 7

    def test_run_known(self):
        src = (
            '@var[p; @argparse.new[]]\n'
            '@argparse.add[p; "--a"]\n'
            '@var[res; @argparse.run_known[p; ["--a", "1", "--extra", "9"]]]'
        )
        g = run(src)
        ns, extra = g["res"]
        assert ns.a == "1" and "--extra" in extra


# ─────────────────────────────────────────────────────────────
# @selectors — modify / count
# ─────────────────────────────────────────────────────────────

class TestSelectorsExpanded:
    def test_count(self):
        a, b = _socket.socketpair()
        try:
            src = (
                '@var[sel; @selectors.new[]]\n'
                '@selectors.watch_read[sel; a]\n'
                '@var[n; @selectors.count[sel]]'
            )
            g = run(src, {"a": a})
            assert g["n"] == 1
            g["sel"].close()
        finally:
            a.close(); b.close()

    def test_modify(self):
        import selectors
        a, b = _socket.socketpair()
        try:
            src = (
                '@var[sel; @selectors.new[]]\n'
                '@selectors.watch_read[sel; a]\n'
                '@selectors.modify[sel; a; @selectors.write[]]\n'
                '@var[m; @selectors.watched[sel]]'
            )
            g = run(src, {"a": a})
            key = g["m"][a.fileno()]
            assert key.events == selectors.EVENT_WRITE
            g["sel"].close()
        finally:
            a.close(); b.close()
