"""
Shell-style lexing for Cruhon — @shlex.*

Wraps Python's `shlex` module: split command lines the way a POSIX shell
would, safely quote arguments, and rejoin token lists. No `@import` needed.

━━━ SPLIT / JOIN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shlex.split[command]      → list of tokens (respects quotes/escapes)
  @shlex.split[command; comments] → split, honoring "#" comments if True
  @shlex.join[tokens]        → safely-quoted single command string

━━━ QUOTE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shlex.quote[s]            → shell-escape a single argument
  @shlex.quote_all[tokens]   → list with every token shell-escaped
"""
from ..registry import register_lib, register_lib_call

_SH = "__import__('shlex')"


def register():
    register_lib("shlex", "shlex")

    register_lib_call("shlex", "split",
        lambda a: (
            f"{_SH}.split({a[0]}, comments={a[1]})"
            if len(a) > 1 else
            f"{_SH}.split({a[0]})"
            if a else "[]"
        ))

    register_lib_call("shlex", "join",
        lambda a: f"{_SH}.join({a[0]})" if a else "''")

    register_lib_call("shlex", "quote",
        lambda a: f"{_SH}.quote(str({a[0]}))" if a else "''")

    register_lib_call("shlex", "quote_all",
        lambda a: f"[{_SH}.quote(str(_t)) for _t in {a[0]}]" if a else "[]")
