"""
TOML reading for Cruhon — @toml.*

Wraps Python's `tomllib` (standard library since 3.11): parse TOML from a
string or file into plain dicts. No `@import` needed.

Note: `tomllib` is read-only. Writing TOML requires a third-party package
(e.g. `tomli_w` or `toml`); use `@config.save` or build the string manually.

━━━ PARSE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @toml.loads[text]          → dict parsed from a TOML string
  @toml.load[path]           → dict parsed from a TOML file

━━━ ACCESS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @toml.get[text; key]       → a top-level value by key
  @toml.get[text; key; dflt] → value by key, or a default if missing
  @toml.keys[text]           → list of top-level keys
  @toml.has[text; key]       → True if the key exists at the top level
"""
from ..registry import register_lib, register_lib_call

_TL = "__import__('tomllib')"


def register():
    register_lib("toml", "tomllib")

    register_lib_call("toml", "loads",
        lambda a: f"{_TL}.loads({a[0]})" if a else "{}")

    register_lib_call("toml", "load",
        lambda a: f"{_TL}.load(open({a[0]}, 'rb'))" if a else "{}")

    register_lib_call("toml", "get",
        lambda a: (
            f"{_TL}.loads({a[0]}).get({a[1]}, {a[2]})"
            if len(a) > 2 else
            f"{_TL}.loads({a[0]}).get({a[1]})"
            if len(a) > 1 else "None"
        ))

    register_lib_call("toml", "keys",
        lambda a: f"list({_TL}.loads({a[0]}).keys())" if a else "[]")

    register_lib_call("toml", "has",
        lambda a: f"({a[1]} in {_TL}.loads({a[0]}))" if len(a) > 1 else "False")
