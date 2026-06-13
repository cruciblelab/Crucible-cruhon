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

━━━ RUN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @httpserver.handle_one[server]  → handle a single request (blocking)
  @httpserver.serve[server]       → serve forever (blocking)
  @httpserver.port[server]        → the port the server is bound to
  @httpserver.close[server]       → shut the server down
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

    # ── Run ───────────────────────────────────────────────────
    register_lib_call("httpserver", "handle_one",
        lambda a: f"{a[0]}.handle_request()")
    register_lib_call("httpserver", "serve",
        lambda a: f"{a[0]}.serve_forever()")
    register_lib_call("httpserver", "port",
        lambda a: f"{a[0]}.server_address[1]")
    register_lib_call("httpserver", "close",
        lambda a: f"{a[0]}.server_close()")
