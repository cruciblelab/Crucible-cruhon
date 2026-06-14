"""
cruhon/core/libs/linecache_.py
==============================
Cached source-line retrieval for Cruhon — @linecache.*

Fetch individual lines from Python source files, with caching.

━━━ GET ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @linecache.line[path; n]        → the n-th line (1-based) as a string
  @linecache.lines[path]          → all lines as a list
  @linecache.clear[]              → clear the cache
"""
from ..registry import register_lib, register_lib_call

_LC = "__import__('linecache')"


def register():
    register_lib("linecache", None)

    register_lib_call("linecache", "line",
        lambda a: f"{_LC}.getline({a[0]}, {a[1]})")
    register_lib_call("linecache", "lines",
        lambda a: f"{_LC}.getlines({a[0]})")
    register_lib_call("linecache", "clear",
        lambda a: f"{_LC}.clearcache()")
