"""
cruhon/core/libs/fnmatch_.py
============================
Fnmatch wrappers for Cruhon — @fnmatch.*

Unix shell-style filename pattern matching. Patterns use * ? [seq] [!seq].
Unlike @glob, this works on strings — no filesystem access.

  @fnmatch.match[name; pattern]       → bool (case-sensitive on Unix)
  @fnmatch.imatch[name; pattern]      → bool (always case-insensitive)
  @fnmatch.filter[names; pattern]     → matching names from list
  @fnmatch.ifilter[names; pattern]    → case-insensitive filter
  @fnmatch.reject[names; pattern]     → names that do NOT match
  @fnmatch.translate[pattern]         → equivalent regex string
  @fnmatch.any_match[name; patterns]  → bool: matches any pattern in list
  @fnmatch.all_match[names; pattern]  → bool: every name matches pattern
"""
from ..registry import register_lib, register_lib_call

_FM = "__import__('fnmatch')"


def register():
    register_lib("fnmatch", None)

    register_lib_call("fnmatch", "match",
        lambda a: f"{_FM}.fnmatch({a[0]}, {a[1]})")

    register_lib_call("fnmatch", "imatch",
        lambda a: f"{_FM}.fnmatch({a[0]}.lower(), {a[1]}.lower())")

    register_lib_call("fnmatch", "filter",
        lambda a: f"{_FM}.filter({a[0]}, {a[1]})")

    register_lib_call("fnmatch", "ifilter",
        lambda a: (
            f"(lambda _ns, _p: {_FM}.filter([_n.lower() for _n in _ns], _p.lower()))({a[0]}, {a[1]})"
        ))

    register_lib_call("fnmatch", "reject",
        lambda a: f"[_n for _n in {a[0]} if not {_FM}.fnmatch(_n, {a[1]})]")

    register_lib_call("fnmatch", "translate",
        lambda a: f"{_FM}.translate({a[0]})")

    register_lib_call("fnmatch", "any_match",
        lambda a: f"any({_FM}.fnmatch({a[0]}, _p) for _p in {a[1]})")

    register_lib_call("fnmatch", "all_match",
        lambda a: f"all({_FM}.fnmatch(_n, {a[1]}) for _n in {a[0]})")
