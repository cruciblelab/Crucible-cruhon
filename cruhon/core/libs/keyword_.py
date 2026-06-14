"""
cruhon/core/libs/keyword_.py
============================
Python keyword inspection for Cruhon — @keyword.*

Check whether a string is a keyword or soft-keyword, and list them all.

━━━ CHECK ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @keyword.is_keyword[s]          → bool: is s a reserved keyword?
  @keyword.is_soft[s]             → bool: is s a soft keyword (match/case)?

━━━ LISTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @keyword.all[]                  → list of all keywords
  @keyword.soft[]                 → list of soft keywords
  @keyword.count[]                → how many reserved keywords exist
"""
from ..registry import register_lib, register_lib_call

_KW = "__import__('keyword')"


def register():
    register_lib("keyword", None)

    register_lib_call("keyword", "is_keyword",
        lambda a: f"{_KW}.iskeyword({a[0]})")
    register_lib_call("keyword", "is_soft",
        lambda a: f"{_KW}.issoftkeyword({a[0]})")
    register_lib_call("keyword", "all",
        lambda a: f"{_KW}.kwlist")
    register_lib_call("keyword", "soft",
        lambda a: f"{_KW}.softkwlist")
    register_lib_call("keyword", "count",
        lambda a: f"len({_KW}.kwlist)")
