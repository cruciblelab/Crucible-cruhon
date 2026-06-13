"""
cruhon/core/libs/ssl_.py
========================
TLS/SSL helpers for Cruhon — @ssl.*

Create SSL contexts, wrap sockets, and inspect server certificates.

━━━ CONTEXTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ssl.context[]                  → secure default client context
  @ssl.unverified[]               → context with verification disabled
  @ssl.server_context[cert; key]  → server context loaded with a cert/key

━━━ WRAP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ssl.wrap[sock; host]           → TLS-wrap a client socket (SNI = host)

━━━ CERTIFICATES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ssl.server_cert[host; port]    → PEM certificate string of a server
  @ssl.cert_dict[host; port]      → parsed certificate dict of a server
  @ssl.verify_paths[]             → default CA file/dir locations
"""
from ..registry import register_lib, register_lib_call

_SS = "__import__('ssl')"
_SK = "__import__('socket')"


def register():
    register_lib("ssl", None)

    # ── Contexts ──────────────────────────────────────────────
    register_lib_call("ssl", "context",
        lambda a: f"{_SS}.create_default_context()")
    register_lib_call("ssl", "unverified",
        lambda a: f"{_SS}._create_unverified_context()")
    register_lib_call("ssl", "server_context",
        lambda a: (
            f"(lambda _c, _k: (lambda _x: (_x.load_cert_chain(_c, _k), _x)[1])"
            f"({_SS}.SSLContext({_SS}.PROTOCOL_TLS_SERVER)))({a[0]}, {a[1]})"
        ))

    # ── Wrap ──────────────────────────────────────────────────
    register_lib_call("ssl", "wrap",
        lambda a: (
            f"{_SS}.create_default_context().wrap_socket({a[0]}, server_hostname={a[1]})"
        ))

    # ── Certificates ──────────────────────────────────────────
    register_lib_call("ssl", "server_cert",
        lambda a: f"{_SS}.get_server_certificate(({a[0]}, {a[1]}))")
    register_lib_call("ssl", "cert_dict",
        lambda a: (
            f"(lambda _h, _p: (lambda _c: _c.wrap_socket({_SK}.create_connection((_h, _p)), "
            f"server_hostname=_h).getpeercert())({_SS}.create_default_context()))({a[0]}, {a[1]})"
        ))
    register_lib_call("ssl", "verify_paths",
        lambda a: f"{_SS}.get_default_verify_paths()")
