"""
cruhon/core/libs/getpass_.py
============================
Secure password / user prompts for Cruhon — @getpass.*

Read secrets from the terminal without echoing, and look up the current
OS login name.

━━━ PASSWORD ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @getpass.ask[]                  → read password (prompt "Password: ")
  @getpass.ask[prompt]            → read password with custom prompt
  @getpass.password[]             → alias of ask
  @getpass.password[prompt]       → alias of ask

━━━ USER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @getpass.user[]                 → current OS login name
"""
from ..registry import register_lib, register_lib_call

_GP = "__import__('getpass')"


def register():
    register_lib("getpass", None)

    register_lib_call("getpass", "ask",
        lambda a: (
            f"{_GP}.getpass({a[0]})" if a else f"{_GP}.getpass()"
        ))

    register_lib_call("getpass", "password",
        lambda a: (
            f"{_GP}.getpass({a[0]})" if a else f"{_GP}.getpass()"
        ))

    register_lib_call("getpass", "user",
        lambda a: f"{_GP}.getuser()")
