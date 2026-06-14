"""
cruhon/core/libs/httpserver_.py
===============================
Tiny HTTP server for Cruhon — @httpserver.*

Spin up a static-file or custom HTTP server in a few calls.

━━━ SERVERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @httpserver.files[port]         → server that serves the current directory
  @httpserver.files[port; dir]    → serve a specific directory
  @httpserver.server[port; handler] → server with a custom handler class
  @httpserver.handler[]           → the SimpleHTTPRequestHandler class

  @httpserver.threaded[port]      → a multi-threaded static-file server
  @httpserver.threaded[port; dir] → … serving a specific directory

━━━ RUN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @httpserver.handle_one[server]  → handle a single request (blocking)
  @httpserver.serve[server]       → serve forever (blocking)
  @httpserver.serve_async[server] → serve forever in a daemon thread → thread
  @httpserver.port[server]        → the port the server is bound to
  @httpserver.close[server]       → shut the server down
  @httpserver.stop[server]        → stop a serve_forever loop
"""
from ..registry import register_lib, register_lib_call

_HS = "__import__('http.server', fromlist=['server'])"
_FN = "__import__('functools')"


def register():
    register_lib("httpserver", None)

    # ── Servers ───────────────────────────────────────────────
    register_lib_call("httpserver", "files",
        lambda a: (
            f"{_HS}.HTTPServer(('', {a[0]}), {_FN}.partial({_HS}.SimpleHTTPRequestHandler, directory={a[1]}))"
            if len(a) > 1 else
            f"{_HS}.HTTPServer(('', {a[0]}), {_HS}.SimpleHTTPRequestHandler)"
        ))
    register_lib_call("httpserver", "server",
        lambda a: f"{_HS}.HTTPServer(('', {a[0]}), {a[1]})")
    register_lib_call("httpserver", "handler",
        lambda a: f"{_HS}.SimpleHTTPRequestHandler")
    register_lib_call("httpserver", "threaded",
        lambda a: (
            f"{_HS}.ThreadingHTTPServer(('', {a[0]}), {_FN}.partial({_HS}.SimpleHTTPRequestHandler, directory={a[1]}))"
            if len(a) > 1 else
            f"{_HS}.ThreadingHTTPServer(('', {a[0]}), {_HS}.SimpleHTTPRequestHandler)"
        ))

    # ── Run ───────────────────────────────────────────────────
    register_lib_call("httpserver", "handle_one",
        lambda a: f"{a[0]}.handle_request()")
    register_lib_call("httpserver", "serve",
        lambda a: f"{a[0]}.serve_forever()")
    register_lib_call("httpserver", "serve_async",
        lambda a: (
            f"(lambda _s: (lambda _t: (_t.start(), _t)[1])"
            f"(__import__('threading').Thread(target=_s.serve_forever, daemon=True)))({a[0]})"
        ))
    register_lib_call("httpserver", "port",
        lambda a: f"{a[0]}.server_address[1]")
    register_lib_call("httpserver", "close",
        lambda a: f"{a[0]}.server_close()")
    register_lib_call("httpserver", "stop",
        lambda a: f"{a[0]}.shutdown()")
