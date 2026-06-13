"""
cruhon/core/libs/multiprocessing_.py
====================================
Process-based parallelism for Cruhon — @multiprocessing.*

Run work across multiple CPU cores. Functions passed to pools must be
importable (defined at module level), not lambdas.

━━━ POOLS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @multiprocessing.cpus[]         → number of available CPU cores
  @multiprocessing.pool[]         → a process Pool (one worker per core)
  @multiprocessing.pool[n]        → a Pool with n workers
  @multiprocessing.map[fn; items] → parallel map, returns a list (one-shot)
  @multiprocessing.starmap[fn; items] → like map but unpacks each tuple

━━━ PRIMITIVES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @multiprocessing.process[fn; args] → a Process targeting fn with args tuple
  @multiprocessing.queue[]        → a process-safe Queue
  @multiprocessing.manager[]      → a Manager for shared objects
  @multiprocessing.lock[]         → a process Lock
"""
from ..registry import register_lib, register_lib_call

_MP = "__import__('multiprocessing')"


def register():
    register_lib("multiprocessing", None)

    # ── Pools ─────────────────────────────────────────────────
    register_lib_call("multiprocessing", "cpus",
        lambda a: f"{_MP}.cpu_count()")
    register_lib_call("multiprocessing", "pool",
        lambda a: f"{_MP}.Pool({a[0]})" if a else f"{_MP}.Pool()")
    register_lib_call("multiprocessing", "map",
        lambda a: (
            f"(lambda _f, _it: (lambda _p: (lambda _r: (_p.close(), _r)[1])(_p.map(_f, _it)))"
            f"({_MP}.Pool()))({a[0]}, {a[1]})"
        ))
    register_lib_call("multiprocessing", "starmap",
        lambda a: (
            f"(lambda _f, _it: (lambda _p: (lambda _r: (_p.close(), _r)[1])(_p.starmap(_f, _it)))"
            f"({_MP}.Pool()))({a[0]}, {a[1]})"
        ))

    # ── Primitives ────────────────────────────────────────────
    register_lib_call("multiprocessing", "process",
        lambda a: (
            f"{_MP}.Process(target={a[0]}, args={a[1]})" if len(a) > 1 else
            f"{_MP}.Process(target={a[0]})"
        ))
    register_lib_call("multiprocessing", "queue",
        lambda a: f"{_MP}.Queue()")
    register_lib_call("multiprocessing", "manager",
        lambda a: f"{_MP}.Manager()")
    register_lib_call("multiprocessing", "lock",
        lambda a: f"{_MP}.Lock()")
