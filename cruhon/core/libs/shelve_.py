"""
cruhon/core/libs/shelve_.py
===========================
Shelve wrappers for Cruhon — @shelve.*

Shelve is a persistent dictionary backed by a dbm file. Keys must be strings;
values can be any picklable Python object.

━━━ HANDLE-BASED (open once, use many times) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shelve.open[path]              → shelf handle
  @shelve.close[shelf]            — sync and close
  @shelve.sync[shelf]             — flush to disk without closing

━━━ ONE-SHOT (auto open → operate → close) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shelve.get[path; key]          → value or None
  @shelve.get[path; key; default] → value or default
  @shelve.set[path; key; value]   — store value
  @shelve.delete[path; key]       — remove key (no error if missing)
  @shelve.has[path; key]          → bool
  @shelve.pop[path; key]          → value, then delete (None if missing)
  @shelve.pop[path; key; default] → value or default, then delete
  @shelve.setdefault[path; key; value]  → existing value or stores+returns default
  @shelve.keys[path]              → list of all keys
  @shelve.values[path]            → list of all values
  @shelve.items[path]             → list of (key, value) tuples
  @shelve.all[path]               → dict of all entries
  @shelve.count[path]             → number of keys
  @shelve.clear[path]             — remove all entries
  @shelve.update[path; dict]      — merge dict into shelf
  @shelve.rename[path; old; new]  — rename a key
  @shelve.increment[path; key]    — numeric += 1
  @shelve.increment[path; key; n] — numeric += n
"""
from ..registry import register_lib, register_lib_call


def register():
    register_lib("shelve", None)

    # ── Handle-based ──────────────────────────────────────────
    register_lib_call("shelve", "open",
        lambda a: f"__import__('shelve').open({a[0]})")

    register_lib_call("shelve", "close",
        lambda a: f"(lambda _s: _s.close())({a[0]})")

    register_lib_call("shelve", "sync",
        lambda a: f"(lambda _s: _s.sync())({a[0]})")

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

    register_lib_call("shelve", "pop",
        lambda a: (
            f"(lambda _p, _k, _d: (lambda _s: (_s.pop(_k, _d), _s.close())[0])(__import__('shelve').open(_p)))({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _p, _k: (lambda _s: (_s.pop(_k, None), _s.close())[0])(__import__('shelve').open(_p)))({a[0]}, {a[1]})"
        ))

    register_lib_call("shelve", "setdefault",
        lambda a: (
            f"(lambda _p, _k, _v: (lambda _s: ("
            f"_s.__setitem__(_k, _v) if _k not in _s else None, _s.get(_k, _v), _s.close())[1])(__import__('shelve').open(_p)))({a[0]}, {a[1]}, {a[2]})"
        ))

    register_lib_call("shelve", "keys",
        lambda a: (
            f"(lambda _p: (lambda _s: (list(_s.keys()), _s.close())[0])(__import__('shelve').open(_p)))({a[0]})"
        ))

    register_lib_call("shelve", "values",
        lambda a: (
            f"(lambda _p: (lambda _s: (list(_s.values()), _s.close())[0])(__import__('shelve').open(_p)))({a[0]})"
        ))

    register_lib_call("shelve", "items",
        lambda a: (
            f"(lambda _p: (lambda _s: (list(_s.items()), _s.close())[0])(__import__('shelve').open(_p)))({a[0]})"
        ))

    register_lib_call("shelve", "all",
        lambda a: (
            f"(lambda _p: (lambda _s: (dict(_s), _s.close())[0])(__import__('shelve').open(_p)))({a[0]})"
        ))

    register_lib_call("shelve", "count",
        lambda a: (
            f"(lambda _p: (lambda _s: (len(list(_s.keys())), _s.close())[0])(__import__('shelve').open(_p)))({a[0]})"
        ))

    register_lib_call("shelve", "clear",
        lambda a: (
            f"(lambda _p: (lambda _s: (_s.clear(), _s.close()))(__import__('shelve').open(_p)))({a[0]})"
        ))

    register_lib_call("shelve", "update",
        lambda a: (
            f"(lambda _p, _d: (lambda _s: (_s.update(_d), _s.close()))(__import__('shelve').open(_p)))({a[0]}, {a[1]})"
        ))

    register_lib_call("shelve", "rename",
        lambda a: (
            f"(lambda _p, _ok, _nk: (lambda _s: ("
            f"_s.__setitem__(_nk, _s[_ok]), _s.pop(_ok), _s.close()) if _ok in _s else _s.close())(__import__('shelve').open(_p)))({a[0]}, {a[1]}, {a[2]})"
        ))

    register_lib_call("shelve", "increment",
        lambda a: (
            f"(lambda _p, _k, _n: (lambda _s: (_s.__setitem__(_k, _s.get(_k, 0) + _n), _s.close()))(__import__('shelve').open(_p)))({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _p, _k: (lambda _s: (_s.__setitem__(_k, _s.get(_k, 0) + 1), _s.close()))(__import__('shelve').open(_p)))({a[0]}, {a[1]})"
        ))
