"""
cruhon/core/libs/selectors_.py
==============================
High-level I/O multiplexing for Cruhon — @selectors.*

Watch many sockets/files at once and react when they become ready —
without low-level select() bit-twiddling.

━━━ SELECTOR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @selectors.new[]                → the best DefaultSelector for this platform
  @selectors.close[sel]           → close the selector

━━━ REGISTER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @selectors.watch_read[sel; obj]      → register obj for read-readiness
  @selectors.watch_write[sel; obj]     → register obj for write-readiness
  @selectors.register[sel; obj; events] → register with explicit event mask
  @selectors.register[sel; obj; events; data] → … with attached data
  @selectors.unwatch[sel; obj]         → stop watching obj

━━━ EVENTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @selectors.read[]               → the EVENT_READ flag
  @selectors.write[]              → the EVENT_WRITE flag
  @selectors.wait[sel]            → block until something is ready → [(key, mask)]
  @selectors.wait[sel; timeout]   → … with a timeout (seconds)
"""
from ..registry import register_lib, register_lib_call

_SL = "__import__('selectors')"


def register():
    register_lib("selectors", None)

    # ── Selector ──────────────────────────────────────────────
    register_lib_call("selectors", "new",
        lambda a: f"{_SL}.DefaultSelector()")
    register_lib_call("selectors", "close",
        lambda a: f"{a[0]}.close()")

    # ── Register ──────────────────────────────────────────────
    register_lib_call("selectors", "watch_read",
        lambda a: f"{a[0]}.register({a[1]}, {_SL}.EVENT_READ)")
    register_lib_call("selectors", "watch_write",
        lambda a: f"{a[0]}.register({a[1]}, {_SL}.EVENT_WRITE)")
    register_lib_call("selectors", "register",
        lambda a: (
            f"{a[0]}.register({a[1]}, {a[2]}, {a[3]})" if len(a) > 3 else
            f"{a[0]}.register({a[1]}, {a[2]})"
        ))
    register_lib_call("selectors", "unwatch",
        lambda a: f"{a[0]}.unregister({a[1]})")

    # ── Events ────────────────────────────────────────────────
    register_lib_call("selectors", "read",
        lambda a: f"{_SL}.EVENT_READ")
    register_lib_call("selectors", "write",
        lambda a: f"{_SL}.EVENT_WRITE")
    register_lib_call("selectors", "wait",
        lambda a: (
            f"{a[0]}.select({a[1]})" if len(a) > 1 else
            f"{a[0]}.select()"
        ))
