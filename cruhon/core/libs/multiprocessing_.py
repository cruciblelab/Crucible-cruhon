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

  @multiprocessing.apply[fn; args] → run fn(*args) in a worker, return result
  @multiprocessing.imap[fn; items] → lazy parallel map collected to a list

━━━ PROCESSES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @multiprocessing.process[fn; args] → a Process targeting fn with args tuple
  @multiprocessing.start[proc]    → start a process (returns the process)
  @multiprocessing.join[proc]     → wait for a process to finish
  @multiprocessing.current[]      → the current Process object
  @multiprocessing.active[]       → list of living child processes
  @multiprocessing.set_start[method] → set start method ("fork"/"spawn")

━━━ PRIMITIVES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @multiprocessing.queue[]        → a process-safe Queue
  @multiprocessing.manager[]      → a Manager for shared objects
  @multiprocessing.lock[]         → a process Lock
  @multiprocessing.event[]        → a process Event
  @multiprocessing.semaphore[n]   → a counting Semaphore
  @multiprocessing.pipe[]         → (conn_a, conn_b) duplex Pipe
  @multiprocessing.value[type; init] → a shared ctypes Value
  @multiprocessing.array[type; seq]  → a shared ctypes Array
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

    register_lib_call("multiprocessing", "apply",
        lambda a: (
            f"(lambda _f, _args: (lambda _p: (lambda _r: (_p.close(), _r)[1])(_p.apply(_f, _args)))"
            f"({_MP}.Pool()))({a[0]}, {a[1]})"
            if len(a) > 1 else
            f"(lambda _f: (lambda _p: (lambda _r: (_p.close(), _r)[1])(_p.apply(_f)))"
            f"({_MP}.Pool()))({a[0]})"
        ))
    register_lib_call("multiprocessing", "imap",
        lambda a: (
            f"(lambda _f, _it: (lambda _p: (lambda _r: (_p.close(), _r)[1])(list(_p.imap(_f, _it))))"
            f"({_MP}.Pool()))({a[0]}, {a[1]})"
        ))

    # ── Processes ─────────────────────────────────────────────
    register_lib_call("multiprocessing", "process",
        lambda a: (
            f"{_MP}.Process(target={a[0]}, args={a[1]})" if len(a) > 1 else
            f"{_MP}.Process(target={a[0]})"
        ))
    register_lib_call("multiprocessing", "start",
        lambda a: f"(lambda _p: (_p.start(), _p)[1])({a[0]})")
    register_lib_call("multiprocessing", "join",
        lambda a: f"{a[0]}.join({a[1]})" if len(a) > 1 else f"{a[0]}.join()")
    register_lib_call("multiprocessing", "current",
        lambda a: f"{_MP}.current_process()")
    register_lib_call("multiprocessing", "active",
        lambda a: f"{_MP}.active_children()")
    register_lib_call("multiprocessing", "set_start",
        lambda a: f"{_MP}.set_start_method({a[0]}, force=True)")

    # ── Primitives ────────────────────────────────────────────
    register_lib_call("multiprocessing", "queue",
        lambda a: f"{_MP}.Queue()")
    register_lib_call("multiprocessing", "manager",
        lambda a: f"{_MP}.Manager()")
    register_lib_call("multiprocessing", "lock",
        lambda a: f"{_MP}.Lock()")
    register_lib_call("multiprocessing", "event",
        lambda a: f"{_MP}.Event()")
    register_lib_call("multiprocessing", "semaphore",
        lambda a: f"{_MP}.Semaphore({a[0]})" if a else f"{_MP}.Semaphore()")
    register_lib_call("multiprocessing", "pipe",
        lambda a: f"{_MP}.Pipe()")
    register_lib_call("multiprocessing", "value",
        lambda a: f"{_MP}.Value({a[0]}, {a[1]})")
    register_lib_call("multiprocessing", "array",
        lambda a: f"{_MP}.Array({a[0]}, {a[1]})")
