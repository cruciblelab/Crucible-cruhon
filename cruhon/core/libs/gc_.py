"""
cruhon/core/libs/gc_.py
=======================
Garbage-collector control for Cruhon — @gc.*

Inspect and steer Python's cyclic garbage collector without @raw.

━━━ COLLECT / TOGGLE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @gc.collect[]                   → run a full collection, returns # collected
  @gc.collect[gen]                → collect a single generation (0/1/2)
  @gc.enable[]                    → turn automatic collection on
  @gc.disable[]                   → turn automatic collection off
  @gc.is_enabled[]                → bool

━━━ INSPECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @gc.count[]                     → (gen0, gen1, gen2) live-object counts
  @gc.stats[]                     → per-generation statistics
  @gc.threshold[]                 → current collection thresholds
  @gc.set_threshold[a; b; c]      → set thresholds
  @gc.objects[]                   → list of all tracked objects
  @gc.referrers[obj]              → objects that refer TO obj
  @gc.referents[obj]              → objects obj refers to
  @gc.is_tracked[obj]             → bool
  @gc.garbage[]                   → list of uncollectable objects

━━━ FREEZE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @gc.freeze[]                    → move tracked objects to permanent gen
  @gc.unfreeze[]                  → undo freeze
"""
from ..registry import register_lib, register_lib_call

_GC = "__import__('gc')"


def register():
    register_lib("gc", None)

    # ── Collect / Toggle ──────────────────────────────────────
    register_lib_call("gc", "collect",
        lambda a: f"{_GC}.collect({a[0]})" if a else f"{_GC}.collect()")
    register_lib_call("gc", "enable", lambda a: f"{_GC}.enable()")
    register_lib_call("gc", "disable", lambda a: f"{_GC}.disable()")
    register_lib_call("gc", "is_enabled", lambda a: f"{_GC}.isenabled()")

    # ── Inspect ───────────────────────────────────────────────
    register_lib_call("gc", "count", lambda a: f"{_GC}.get_count()")
    register_lib_call("gc", "stats", lambda a: f"{_GC}.get_stats()")
    register_lib_call("gc", "threshold", lambda a: f"{_GC}.get_threshold()")
    register_lib_call("gc", "set_threshold",
        lambda a: f"{_GC}.set_threshold({', '.join(a)})")
    register_lib_call("gc", "objects", lambda a: f"{_GC}.get_objects()")
    register_lib_call("gc", "referrers",
        lambda a: f"{_GC}.get_referrers({a[0]})")
    register_lib_call("gc", "referents",
        lambda a: f"{_GC}.get_referents({a[0]})")
    register_lib_call("gc", "is_tracked",
        lambda a: f"{_GC}.is_tracked({a[0]})")
    register_lib_call("gc", "garbage", lambda a: f"{_GC}.garbage")

    # ── Freeze ────────────────────────────────────────────────
    register_lib_call("gc", "freeze", lambda a: f"{_GC}.freeze()")
    register_lib_call("gc", "unfreeze", lambda a: f"{_GC}.unfreeze()")
