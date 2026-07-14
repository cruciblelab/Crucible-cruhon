"""pytest configuration for Cruhon tests."""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

# Ensure the package root (one level above cruhon/) is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class _LocalHttpbinHandler(BaseHTTPRequestHandler):
    """Minimal stand-in for httpbin.org's /get and /post — just enough
    for @http.* tests that need a real requests.get/post round trip
    without depending on a live third-party service staying up."""

    def _send_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send_json({"args": {}, "url": self.path})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw) if raw else {}
        except ValueError:
            data = {}
        self._send_json({"json": data, "url": self.path})

    def log_message(self, format, *args):
        pass  # silence default request logging to stderr


@pytest.fixture(scope="session")
def local_httpbin():
    """Base URL of a local httpbin-like server, e.g. "http://127.0.0.1:PORT"."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _LocalHttpbinHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
