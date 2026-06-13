"""
cruhon/core/libs/pop3_.py
=========================
POP3 mail retrieval for Cruhon — @pop3.*

Connect to a POP3 mailbox, count messages and download them.

━━━ CONNECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @pop3.connect[host]             → POP3 connection (plain)
  @pop3.connect[host; port]       → on a custom port
  @pop3.connect_ssl[host]         → POP3 over SSL
  @pop3.login[pop; user; pass]    → authenticate
  @pop3.quit[pop]                 → commit deletions and disconnect

━━━ MAILBOX ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @pop3.count[pop]                → number of messages
  @pop3.size[pop]                 → total mailbox size in bytes
  @pop3.list[pop]                 → per-message (number, size) listing
  @pop3.get[pop; n]               → raw lines of message n
  @pop3.text[pop; n]              → message n decoded as a single string
  @pop3.delete[pop; n]            → mark message n for deletion
"""
from ..registry import register_lib, register_lib_call

_PP = "__import__('poplib')"


def register():
    register_lib("pop3", None)

    # ── Connect ───────────────────────────────────────────────
    register_lib_call("pop3", "connect",
        lambda a: (
            f"{_PP}.POP3({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_PP}.POP3({a[0]})"
        ))
    register_lib_call("pop3", "connect_ssl",
        lambda a: (
            f"{_PP}.POP3_SSL({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_PP}.POP3_SSL({a[0]})"
        ))
    register_lib_call("pop3", "login",
        lambda a: (
            f"(lambda _p, _u, _w: (_p.user(_u), _p.pass_(_w))[1])({a[0]}, {a[1]}, {a[2]})"
        ))
    register_lib_call("pop3", "quit",
        lambda a: f"{a[0]}.quit()")

    # ── Mailbox ───────────────────────────────────────────────
    register_lib_call("pop3", "count",
        lambda a: f"{a[0]}.stat()[0]")
    register_lib_call("pop3", "size",
        lambda a: f"{a[0]}.stat()[1]")
    register_lib_call("pop3", "list",
        lambda a: f"{a[0]}.list()[1]")
    register_lib_call("pop3", "get",
        lambda a: f"{a[0]}.retr({a[1]})[1]")
    register_lib_call("pop3", "text",
        lambda a: (
            f"(lambda _p, _n: b'\\n'.join(_p.retr(_n)[1]).decode('utf-8', 'replace'))({a[0]}, {a[1]})"
        ))
    register_lib_call("pop3", "delete",
        lambda a: f"{a[0]}.dele({a[1]})")
