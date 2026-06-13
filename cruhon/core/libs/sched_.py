"""
cruhon/core/libs/sched_.py
==========================
Event scheduling for Cruhon — @sched.*

Queue callables to run after a delay (or at an absolute time) and run the
queue.

━━━ SCHEDULER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sched.new[]                    → a scheduler using real wall-clock time
  @sched.run[s]                   → run all events (blocks until done)

━━━ EVENTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sched.after[s; delay; fn]      → run fn after `delay` seconds (priority 1)
  @sched.after[s; delay; prio; fn]→ … with an explicit priority
  @sched.at[s; when; fn]          → run fn at an absolute time()
  @sched.cancel[s; event]         → cancel a scheduled event

━━━ STATE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sched.empty[s]                 → bool: is the queue empty
  @sched.queue[s]                 → list of pending events
"""
from ..registry import register_lib, register_lib_call

_SC = "__import__('sched')"


def register():
    register_lib("sched", None)

    # ── Scheduler ─────────────────────────────────────────────
    register_lib_call("sched", "new",
        lambda a: f"{_SC}.scheduler(__import__('time').time, __import__('time').sleep)")
    register_lib_call("sched", "run",
        lambda a: f"{a[0]}.run()")

    # ── Events ────────────────────────────────────────────────
    register_lib_call("sched", "after",
        lambda a: (
            f"{a[0]}.enter({a[1]}, {a[2]}, {a[3]})" if len(a) > 3 else
            f"{a[0]}.enter({a[1]}, 1, {a[2]})"
        ))
    register_lib_call("sched", "at",
        lambda a: f"{a[0]}.enterabs({a[1]}, 1, {a[2]})")
    register_lib_call("sched", "cancel",
        lambda a: f"{a[0]}.cancel({a[1]})")

    # ── State ─────────────────────────────────────────────────
    register_lib_call("sched", "empty",
        lambda a: f"{a[0]}.empty()")
    register_lib_call("sched", "queue",
        lambda a: f"{a[0]}.queue")
