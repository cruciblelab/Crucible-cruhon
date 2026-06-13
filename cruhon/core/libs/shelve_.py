"""
cruhon/core/libs/shelve_.py
===========================
Shelve wrappers for Cruhon — @shelve.*

Shelve is a persistent dictionary backed by a file. Open once and use like a
dict, or use the one-shot helpers that open/close automatically.

━━━ HANDLE-BASED ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shelve.open[path]          → shelf handle (use with @with or close manually)
  @shelve.close[shelf]        — close and sync

━━━ ONE-SHOT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shelve.get[path; key]              → value or None
  @shelve.get[path; key; default]     → value or default
  @shelve.set[path; key; value]       — store value
  @shelve.delete[path; key]           — remove key
  @shelve.has[path; key]              → bool
  @shelve.keys[path]                  → list of keys
  @shelve.all[path]                   → dict of all items
  @shelve.clear[path]                 — remove all entries
  @shelve.update[path; dict]          — merge dict into shelf
  @shelve.count[path]                 → number of keys
"""
from ..registry import register_lib, register_lib_call


def register():
    register_lib("shelve", None)

    # ── Handle-based ──────────────────────────────────────────
    register_lib_call("shelve", "open",
        lambda a: f"__import__('shelve').open({a[0]})")

    register_lib_call("shelve", "close",
        lambda a: f"(lambda _s: _s.close())({a[0]})")

    # ── One-shot ──────────────────────────────────────────────
    register_lib_call("shelve", "get",
        lambda a: (
            f"(lambda _p, _k, _d: (lambda _s: (_s.get(_k, _d), _s.close())[0])(__import__('shelve').open(_p)))({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _p, _k: (lambda _s: (_s.get(_k), _s.close())[0])(__import__('shelve').open(_p)))({a[0]}, {a[1]})"
        ))

    register_lib_call("shelve", "set",
        lambda a: (
            f"(lambda _p, _k, _v: (lambda _s: (_s.__setitem__(_k, _v), _s.close()))(__import__('shelve').open(_p)))({a[0]}, {a[1]}, {a[2]})"
        ))

    register_lib_call("shelve", "delete",
        lambda a: (
            f"(lambda _p, _k: (lambda _s: (_s.pop(_k, None), _s.close()))(__import__('shelve').open(_p)))({a[0]}, {a[1]})"
        ))

    register_lib_call("shelve", "has",
        lambda a: (
            f"(lambda _p, _k: (lambda _s: (_k in _s, _s.close())[0])(__import__('shelve').open(_p)))({a[0]}, {a[1]})"
        ))

    register_lib_call("shelve", "keys",
        lambda a: (
            f"(lambda _p: (lambda _s: (list(_s.keys()), _s.close())[0])(__import__('shelve').open(_p)))({a[0]})"
        ))

    register_lib_call("shelve", "all",
        lambda a: (
            f"(lambda _p: (lambda _s: (dict(_s), _s.close())[0])(__import__('shelve').open(_p)))({a[0]})"
        ))

    register_lib_call("shelve", "clear",
        lambda a: (
            f"(lambda _p: (lambda _s: (_s.clear(), _s.close()))(__import__('shelve').open(_p)))({a[0]})"
        ))

    register_lib_call("shelve", "update",
        lambda a: (
            f"(lambda _p, _d: (lambda _s: (_s.update(_d), _s.close()))(__import__('shelve').open(_p)))({a[0]}, {a[1]})"
        ))

    register_lib_call("shelve", "count",
        lambda a: (
            f"(lambda _p: (lambda _s: (len(list(_s.keys())), _s.close())[0])(__import__('shelve').open(_p)))({a[0]})"
        ))
