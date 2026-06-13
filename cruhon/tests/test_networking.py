"""
Tests for Networking namespaces:
@socket, @ssl, @ftp, @pop3, @xmlrpc, @httpserver, @selectors

Network-touching tests use loopback only; stateless helpers are tested
directly. No external hosts are contacted.
"""
import socket as _socket
import ssl as _ssl
import threading
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
    """Transpile + compile only (no execution) — for code needing a live server."""
    compile(transpile(src), "<test>", "exec")
    return True


# ─────────────────────────────────────────────────────────────
# @socket
# ─────────────────────────────────────────────────────────────

class TestSocket:
    def test_hostname(self):
        g = run('@var[h; @socket.hostname[]]')
        assert g["h"] == _socket.gethostname()

    def test_host_to_ip_localhost(self):
        g = run('@var[ip; @socket.host_to_ip["localhost"]]')
        assert g["ip"].startswith("127.") or g["ip"] == "::1"

    def test_free_port(self):
        g = run('@var[p; @socket.free_port[]]')
        assert isinstance(g["p"], int) and 0 < g["p"] < 65536

    def test_is_open_true(self):
        srv = _socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]
        try:
            g = run(f'@var[b; @socket.is_open["127.0.0.1"; {port}]]')
            assert g["b"] is True
        finally:
            srv.close()

    def test_is_open_false(self):
        # find a free port, close it, then probe — should be closed
        s = _socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        g = run(f'@var[b; @socket.is_open["127.0.0.1"; {port}; 1]]')
        assert g["b"] is False

    def test_connect_send_recv(self):
        srv = _socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]

        def echo():
            conn, _ = srv.accept()
            data = conn.recv(64)
            conn.sendall(data.upper())
            conn.close()

        t = threading.Thread(target=echo)
        t.start()
        try:
            src = (
                f'@var[s; @socket.connect["127.0.0.1"; {port}]]\n'
                f'@socket.send[s; b"ping"]\n'
                f'@var[r; @socket.recv[s; 64]]\n'
                f'@socket.close[s]'
            )
            g = run(src)
            assert g["r"] == b"PING"
        finally:
            t.join()
            srv.close()


# ─────────────────────────────────────────────────────────────
# @ssl
# ─────────────────────────────────────────────────────────────

class TestSsl:
    def test_context(self):
        g = run('@var[c; @ssl.context[]]')
        assert isinstance(g["c"], _ssl.SSLContext)

    def test_unverified(self):
        g = run('@var[c; @ssl.unverified[]]')
        assert g["c"].verify_mode == _ssl.CERT_NONE

    def test_verify_paths(self):
        g = run('@var[p; @ssl.verify_paths[]]')
        assert hasattr(g["p"], "cafile")


# ─────────────────────────────────────────────────────────────
# @ftp
# ─────────────────────────────────────────────────────────────

class TestFtp:
    def test_new(self):
        import ftplib
        g = run('@var[f; @ftp.new[]]')
        assert isinstance(g["f"], ftplib.FTP)

    def test_connect_compiles(self):
        assert compiles('@var[f; @ftp.connect["ftp.example.com"; "user"; "pw"]]')

    def test_download_compiles(self):
        assert compiles('@ftp.download[f; "remote.txt"; "local.txt"]')


# ─────────────────────────────────────────────────────────────
# @pop3
# ─────────────────────────────────────────────────────────────

class TestPop3:
    def test_connect_compiles(self):
        assert compiles('@var[p; @pop3.connect["mail.example.com"]]')

    def test_login_compiles(self):
        assert compiles('@pop3.login[p; "user"; "pw"]')

    def test_text_compiles(self):
        assert compiles('@var[t; @pop3.text[p; 1]]')


# ─────────────────────────────────────────────────────────────
# @xmlrpc
# ─────────────────────────────────────────────────────────────

class TestXmlrpc:
    def test_client(self):
        import xmlrpc.client
        g = run('@var[c; @xmlrpc.client["http://localhost:9/RPC2"]]')
        assert isinstance(g["c"], xmlrpc.client.ServerProxy)

    def test_dumps_loads_roundtrip(self):
        src = (
            '@var[x; @xmlrpc.dumps[(1, 2); "add"]]\n'
            '@var[r; @xmlrpc.loads[x]]'
        )
        g = run(src)
        assert g["r"][0] == (1, 2) and g["r"][1] == "add"

    def test_binary(self):
        import xmlrpc.client
        g = run('@var[b; @xmlrpc.binary[b"hi"]]')
        assert isinstance(g["b"], xmlrpc.client.Binary)
        assert g["b"].data == b"hi"


# ─────────────────────────────────────────────────────────────
# @httpserver
# ─────────────────────────────────────────────────────────────

class TestHttpServer:
    def test_handler(self):
        import http.server
        g = run('@var[h; @httpserver.handler[]]')
        assert g["h"] is http.server.SimpleHTTPRequestHandler

    def test_serve_files_loopback(self, tmp_path):
        (tmp_path / "hi.txt").write_text("hello cruhon")
        src = (
            f'@var[srv; @httpserver.files[0; "{tmp_path}"]]\n'
            f'@var[port; @httpserver.port[srv]]'
        )
        g = run(src)
        srv = g["srv"]
        port = g["port"]
        try:
            t = threading.Thread(target=lambda: run('@httpserver.handle_one[srv]', {"srv": srv}))
            t.start()
            data = urllib.request.urlopen(f"http://127.0.0.1:{port}/hi.txt", timeout=5).read()
            assert data == b"hello cruhon"
            t.join()
        finally:
            run('@httpserver.close[srv]', {"srv": srv})


# ─────────────────────────────────────────────────────────────
# @selectors
# ─────────────────────────────────────────────────────────────

class TestSelectors:
    def test_new_and_events(self):
        import selectors
        g = run('@var[s; @selectors.new[]]\n@var[r; @selectors.read[]]')
        assert g["r"] == selectors.EVENT_READ
        g["s"].close()

    def test_watch_and_wait(self):
        a, b = _socket.socketpair()
        try:
            src = (
                '@var[sel; @selectors.new[]]\n'
                '@selectors.watch_read[sel; a]\n'
                '@var[ready; @selectors.wait[sel; 1]]'
            )
            b.sendall(b"x")  # make `a` readable
            g = run(src, {"a": a})
            assert len(g["ready"]) == 1
            g["sel"].close()
        finally:
            a.close()
            b.close()
