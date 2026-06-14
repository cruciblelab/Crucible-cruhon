"""
cruhon/core/libs/tracemalloc_.py
================================
Memory allocation tracing for Cruhon — @tracemalloc.*

Find out which Python objects are using the most memory.

━━━ CONTROL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @tracemalloc.start[]            → begin tracing
  @tracemalloc.start[frames]      → trace with N frame depth
  @tracemalloc.stop[]             → stop tracing and release data
  @tracemalloc.is_tracing[]       → bool

━━━ SNAPSHOTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @tracemalloc.snapshot[]         → take a Snapshot of current allocations
  @tracemalloc.top[n]             → (file, line, size_bytes) for n biggest
  @tracemalloc.top[n; snap]       → top-n from an existing Snapshot
  @tracemalloc.diff[snap1; snap2] → (file, line, size_diff) list

━━━ CURRENT USAGE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @tracemalloc.current[]          → (current_bytes, peak_bytes) tuple
"""
from ..registry import register_lib, register_lib_call

_TM = "__import__('tracemalloc')"


def register():
    register_lib("tracemalloc", None)

    # ── Control ───────────────────────────────────────────────
    register_lib_call("tracemalloc", "start",
        lambda a: f"{_TM}.start({a[0]})" if a else f"{_TM}.start()")
    register_lib_call("tracemalloc", "stop",
        lambda a: f"{_TM}.stop()")
    register_lib_call("tracemalloc", "is_tracing",
        lambda a: f"{_TM}.is_tracing()")

    # ── Snapshots ─────────────────────────────────────────────
    register_lib_call("tracemalloc", "snapshot",
        lambda a: f"{_TM}.take_snapshot()")
    register_lib_call("tracemalloc", "top",
        lambda a: (
            f"[(_s.traceback[0].filename, _s.traceback[0].lineno, _s.size) "
            f"for _s in {a[1]}.statistics('lineno')[:{a[0]}]]"
            if len(a) > 1 else
            f"(lambda _snap: [(_s.traceback[0].filename, _s.traceback[0].lineno, _s.size) "
            f"for _s in _snap.statistics('lineno')[:{a[0]}]])({_TM}.take_snapshot())"
        ))
    register_lib_call("tracemalloc", "diff",
        lambda a: (
            f"[(_s.traceback[0].filename, _s.traceback[0].lineno, _s.size_diff) "
            f"for _s in {a[1]}.compare_to({a[0]}, 'lineno')]"
        ))

    # ── Current usage ─────────────────────────────────────────
    register_lib_call("tracemalloc", "current",
        lambda a: f"{_TM}.get_traced_memory()")
