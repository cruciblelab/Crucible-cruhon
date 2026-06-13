"""
cruhon/core/libs/xmlrpc_.py
===========================
XML-RPC client for Cruhon — @xmlrpc.*

Call remote procedures over XML-RPC and encode/decode payloads.

━━━ CLIENT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @xmlrpc.client[url]             → a ServerProxy for url
  @xmlrpc.call[proxy; method]     → call a remote method with no args
  @xmlrpc.call[proxy; method; args] → call with a list/tuple of args

━━━ ENCODE / DECODE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @xmlrpc.dumps[params; method]   → XML request string for a method call
  @xmlrpc.loads[xml]              → (params, method-name) from XML
  @xmlrpc.binary[bytes]           → wrap bytes for transport
  @xmlrpc.datetime[value]         → wrap a datetime value
"""
from ..registry import register_lib, register_lib_call

_XR = "__import__('xmlrpc.client', fromlist=['client'])"


def register():
    register_lib("xmlrpc", None)

    # ── Client ────────────────────────────────────────────────
    register_lib_call("xmlrpc", "client",
        lambda a: f"{_XR}.ServerProxy({a[0]})")
    register_lib_call("xmlrpc", "call",
        lambda a: (
            f"getattr({a[0]}, {a[1]})(*{a[2]})" if len(a) > 2 else
            f"getattr({a[0]}, {a[1]})()"
        ))

    # ── Encode / Decode ───────────────────────────────────────
    register_lib_call("xmlrpc", "dumps",
        lambda a: f"{_XR}.dumps({a[0]}, {a[1]})")
    register_lib_call("xmlrpc", "loads",
        lambda a: f"{_XR}.loads({a[0]})")
    register_lib_call("xmlrpc", "binary",
        lambda a: f"{_XR}.Binary({a[0]})")
    register_lib_call("xmlrpc", "datetime",
        lambda a: f"{_XR}.DateTime({a[0]})")
