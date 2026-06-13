"""
cruhon/core/libs/weakref_.py
============================
Weak references for Cruhon — @weakref.*

Reference objects without keeping them alive — useful for caches and
back-references that must not create cycles.

━━━ CREATE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @weakref.ref[obj]               → a weak reference (call it to deref)
  @weakref.proxy[obj]             → a transparent weak proxy

━━━ USE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @weakref.deref[ref]             → the object, or None if dead
  @weakref.is_alive[ref]          → bool: is the referent still alive
  @weakref.count[obj]             → number of weak references to obj
  @weakref.refs[obj]              → list of weak references to obj

━━━ CONTAINERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @weakref.dict[]                 → WeakValueDictionary
  @weakref.key_dict[]             → WeakKeyDictionary
  @weakref.set[]                  → WeakSet
"""
from ..registry import register_lib, register_lib_call

_WR = "__import__('weakref')"


def register():
    register_lib("weakref", None)

    # ── Create ────────────────────────────────────────────────
    register_lib_call("weakref", "ref",
        lambda a: f"{_WR}.ref({a[0]})")
    register_lib_call("weakref", "proxy",
        lambda a: f"{_WR}.proxy({a[0]})")

    # ── Use ───────────────────────────────────────────────────
    register_lib_call("weakref", "deref",
        lambda a: f"{a[0]}()")
    register_lib_call("weakref", "is_alive",
        lambda a: f"({a[0]}() is not None)")
    register_lib_call("weakref", "count",
        lambda a: f"{_WR}.getweakrefcount({a[0]})")
    register_lib_call("weakref", "refs",
        lambda a: f"{_WR}.getweakrefs({a[0]})")

    # ── Containers ────────────────────────────────────────────
    register_lib_call("weakref", "dict",
        lambda a: f"{_WR}.WeakValueDictionary()")
    register_lib_call("weakref", "key_dict",
        lambda a: f"{_WR}.WeakKeyDictionary()")
    register_lib_call("weakref", "set",
        lambda a: f"{_WR}.WeakSet()")
