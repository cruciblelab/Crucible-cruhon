"""
cruhon/core/libs/futures_.py
============================
High-level async execution for Cruhon — @futures.*

Run callables in thread or process pools and collect their results via
concurrent.futures.

━━━ EXECUTORS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @futures.threads[]              → a ThreadPoolExecutor
  @futures.threads[n]             → with n worker threads
  @futures.processes[]            → a ProcessPoolExecutor
  @futures.processes[n]           → with n worker processes
  @futures.shutdown[ex]           → wait for tasks and shut down

━━━ ONE-SHOT MAP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @futures.thread_map[fn; items]  → parallel map over threads → list
  @futures.process_map[fn; items] → parallel map over processes → list

━━━ FUTURES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @futures.submit[ex; fn; args]   → schedule fn(*args), returns a Future
  @futures.result[future]         → block for and return the result
  @futures.done[future]           → bool: has the future finished
  @futures.wait[futures]          → block until all futures complete
"""
from ..registry import register_lib, register_lib_call

_CF = "__import__('concurrent.futures', fromlist=['futures'])"


def register():
    register_lib("futures", None)

    # ── Executors ─────────────────────────────────────────────
    register_lib_call("futures", "threads",
        lambda a: f"{_CF}.ThreadPoolExecutor({a[0]})" if a else f"{_CF}.ThreadPoolExecutor()")
    register_lib_call("futures", "processes",
        lambda a: f"{_CF}.ProcessPoolExecutor({a[0]})" if a else f"{_CF}.ProcessPoolExecutor()")
    register_lib_call("futures", "shutdown",
        lambda a: f"{a[0]}.shutdown()")

    # ── One-shot map ──────────────────────────────────────────
    register_lib_call("futures", "thread_map",
        lambda a: (
            f"(lambda _f, _it: (lambda _e: (lambda _r: (_e.shutdown(), _r)[1])(list(_e.map(_f, _it))))"
            f"({_CF}.ThreadPoolExecutor()))({a[0]}, {a[1]})"
        ))
    register_lib_call("futures", "process_map",
        lambda a: (
            f"(lambda _f, _it: (lambda _e: (lambda _r: (_e.shutdown(), _r)[1])(list(_e.map(_f, _it))))"
            f"({_CF}.ProcessPoolExecutor()))({a[0]}, {a[1]})"
        ))

    # ── Futures ───────────────────────────────────────────────
    register_lib_call("futures", "submit",
        lambda a: (
            f"{a[0]}.submit({a[1]}, *{a[2]})" if len(a) > 2 else
            f"{a[0]}.submit({a[1]})"
        ))
    register_lib_call("futures", "result",
        lambda a: f"{a[0]}.result()")
    register_lib_call("futures", "done",
        lambda a: f"{a[0]}.done()")
    register_lib_call("futures", "wait",
        lambda a: f"{_CF}.wait({a[0]})")
