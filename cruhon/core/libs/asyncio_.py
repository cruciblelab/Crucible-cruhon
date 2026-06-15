"""
cruhon/core/libs/asyncio_.py
============================
Async I/O and event loop for Cruhon — @asyncio.*

Write and run coroutines, tasks, and async primitives without touching the
event loop directly.

━━━ RUN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @asyncio.run[coro]              → run a coroutine to completion
  @asyncio.sleep[secs]            → await asyncio.sleep(secs)
  @asyncio.gather[c1; c2; ...]   → run coroutines concurrently
  @asyncio.wait_for[coro; secs]  → run with timeout; raises TimeoutError

━━━ TASKS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @asyncio.task[coro]             → asyncio.create_task(coro)
  @asyncio.cancel[task]           → task.cancel()
  @asyncio.done[task]             → task.done()
  @asyncio.result[task]           → task.result()
  @asyncio.all_tasks[]            → asyncio.all_tasks()
  @asyncio.current_task[]         → asyncio.current_task()
  @asyncio.shield[coro]           → asyncio.shield(coro)
  @asyncio.ensure[coro]           → asyncio.ensure_future(coro)

━━━ EVENT LOOP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @asyncio.loop[]                 → asyncio.get_event_loop()
  @asyncio.new_loop[]             → asyncio.new_event_loop()
  @asyncio.set_loop[loop]         → asyncio.set_event_loop(loop)
  @asyncio.run_loop[loop; coro]   → loop.run_until_complete(coro)
  @asyncio.close_loop[loop]       → loop.close()

━━━ SYNC PRIMITIVES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @asyncio.lock[]                 → asyncio.Lock()
  @asyncio.event[]                → asyncio.Event()
  @asyncio.condition[]            → asyncio.Condition()
  @asyncio.semaphore[n]           → asyncio.Semaphore(n)
  @asyncio.queue[]                → asyncio.Queue()
  @asyncio.queue[maxsize]         → asyncio.Queue(maxsize)

━━━ STREAMS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @asyncio.open[host; port]       → await asyncio.open_connection(host, port)
  @asyncio.serve[host; port; cb]  → await asyncio.start_server(cb, host, port)

━━━ UTILITIES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @asyncio.timeout[secs]          → asyncio.timeout(secs) context manager (3.11+)
  @asyncio.iscoroutine[obj]       → asyncio.iscoroutine(obj)
  @asyncio.isfuture[obj]          → asyncio.isfuture(obj)
  @asyncio.istask[obj]            → isinstance(obj, asyncio.Task)
"""
from ..registry import register_lib, register_lib_call

_AIO = "__import__('asyncio')"


def register():
    register_lib("asyncio", None)

    # ── Run ───────────────────────────────────────────────────
    register_lib_call("asyncio", "run",
        lambda a: f"{_AIO}.run({a[0]})")
    register_lib_call("asyncio", "sleep",
        lambda a: f"await {_AIO}.sleep({a[0]})")
    register_lib_call("asyncio", "gather",
        lambda a: f"await {_AIO}.gather({', '.join(a)})")
    register_lib_call("asyncio", "wait_for",
        lambda a: f"await {_AIO}.wait_for({a[0]}, timeout={a[1]})")

    # ── Tasks ─────────────────────────────────────────────────
    register_lib_call("asyncio", "task",
        lambda a: f"{_AIO}.create_task({a[0]})")
    register_lib_call("asyncio", "cancel",
        lambda a: f"{a[0]}.cancel()")
    register_lib_call("asyncio", "done",
        lambda a: f"{a[0]}.done()")
    register_lib_call("asyncio", "result",
        lambda a: f"{a[0]}.result()")
    register_lib_call("asyncio", "all_tasks",
        lambda a: f"{_AIO}.all_tasks()")
    register_lib_call("asyncio", "current_task",
        lambda a: f"{_AIO}.current_task()")
    register_lib_call("asyncio", "shield",
        lambda a: f"{_AIO}.shield({a[0]})")
    register_lib_call("asyncio", "ensure",
        lambda a: f"{_AIO}.ensure_future({a[0]})")

    # ── Event loop ────────────────────────────────────────────
    register_lib_call("asyncio", "loop",
        lambda a: f"{_AIO}.get_event_loop()")
    register_lib_call("asyncio", "new_loop",
        lambda a: f"{_AIO}.new_event_loop()")
    register_lib_call("asyncio", "set_loop",
        lambda a: f"{_AIO}.set_event_loop({a[0]})")
    register_lib_call("asyncio", "run_loop",
        lambda a: f"{a[0]}.run_until_complete({a[1]})")
    register_lib_call("asyncio", "close_loop",
        lambda a: f"{a[0]}.close()")

    # ── Sync primitives ───────────────────────────────────────
    register_lib_call("asyncio", "lock",
        lambda a: f"{_AIO}.Lock()")
    register_lib_call("asyncio", "event",
        lambda a: f"{_AIO}.Event()")
    register_lib_call("asyncio", "condition",
        lambda a: f"{_AIO}.Condition()")
    register_lib_call("asyncio", "semaphore",
        lambda a: f"{_AIO}.Semaphore({a[0]})" if a else f"{_AIO}.Semaphore()")
    register_lib_call("asyncio", "queue",
        lambda a: f"{_AIO}.Queue({a[0]})" if a else f"{_AIO}.Queue()")

    # ── Streams ───────────────────────────────────────────────
    register_lib_call("asyncio", "open",
        lambda a: f"await {_AIO}.open_connection({a[0]}, {a[1]})")
    register_lib_call("asyncio", "serve",
        lambda a: f"await {_AIO}.start_server({a[2]}, {a[0]}, {a[1]})")

    # ── Utilities ─────────────────────────────────────────────
    register_lib_call("asyncio", "timeout",
        lambda a: f"{_AIO}.timeout({a[0]})")
    register_lib_call("asyncio", "iscoroutine",
        lambda a: f"{_AIO}.iscoroutine({a[0]})")
    register_lib_call("asyncio", "isfuture",
        lambda a: f"{_AIO}.isfuture({a[0]})")
    register_lib_call("asyncio", "istask",
        lambda a: f"isinstance({a[0]}, {_AIO}.Task)")
