"""
cruhon-schedule — lightweight asyncio scheduler  (@schedule.*)
==============================================================
Run code on a timer with no external dependencies. Cron support is optional
(uses `croniter` only if it is installed).

━━━ DEFINE JOBS (block commands) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @schedule.every[seconds=30] ... @end       # every 30 seconds
  @schedule.every[minutes=5]  ... @end
  @schedule.every[hours=1]    ... @end
  @schedule.daily["09:00"]    ... @end        # every day at 09:00
  @schedule.weekly[monday; "09:00"] ... @end  # every Monday at 09:00
  @schedule.at["2025-12-31 23:59"]  ... @end  # one-shot at a datetime
  @schedule.cron["0 9 * * *"] ... @end        # cron (needs croniter)

━━━ CONTROL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @schedule.start[]          # launch all defined jobs (call once, in async ctx)
  @schedule.stop[]           # cancel all running jobs
  @schedule.count[]          # number of registered jobs

Inside a Discord bot, call @schedule.start[] from @discord.on[ready].
"""
from __future__ import annotations

_BLOCKS = {"every", "daily", "weekly", "at", "cron"}
_WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
}

_job_counter = [0]


def _preprocess(source: str) -> str:
    for cmd in _BLOCKS:
        source = source.replace(f"@schedule.{cmd}[", f"@_sch_{cmd}[")
    return source


# ─────────────────────────────────────────────────────────────
# RUNTIME SCHEDULER — injected as __scheduler__
# ─────────────────────────────────────────────────────────────

class _CruhonScheduler:
    def __init__(self):
        self._jobs = []     # (kind, spec, coro_fn)
        self._tasks = []

    # decorators used by generated code
    def every(self, seconds=0, minutes=0, hours=0):
        total = seconds + minutes * 60 + hours * 3600
        def deco(fn):
            self._jobs.append(("every", max(1, total), fn)); return fn
        return deco

    def daily(self, time_str):
        def deco(fn):
            self._jobs.append(("daily", time_str, fn)); return fn
        return deco

    def weekly(self, weekday, time_str):
        def deco(fn):
            self._jobs.append(("weekly", (weekday, time_str), fn)); return fn
        return deco

    def at(self, when):
        def deco(fn):
            self._jobs.append(("at", when, fn)); return fn
        return deco

    def cron(self, expr):
        def deco(fn):
            self._jobs.append(("cron", expr, fn)); return fn
        return deco

    # control
    def count(self):
        return len(self._jobs)

    def start(self):
        import asyncio
        loop = asyncio.get_event_loop()
        for kind, spec, fn in self._jobs:
            self._tasks.append(loop.create_task(self._run(kind, spec, fn)))
        return len(self._tasks)

    def stop(self):
        for t in self._tasks:
            t.cancel()
        self._tasks.clear()

    # ── runners ──────────────────────────────────────────────
    @staticmethod
    def _parse_hm(time_str):
        hh, mm = (list(map(int, str(time_str).split(":"))) + [0])[:2]
        return hh, mm

    @staticmethod
    def _weekday_num(name):
        if isinstance(name, int):
            return name % 7
        return _WEEKDAYS.get(str(name).strip().lower(), 0)

    async def _run(self, kind, spec, fn):
        import asyncio
        import datetime as _dt

        if kind == "every":
            while True:
                await asyncio.sleep(spec)
                await fn()

        elif kind == "daily":
            hh, mm = self._parse_hm(spec)
            while True:
                now = _dt.datetime.now()
                target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                if target <= now:
                    target += _dt.timedelta(days=1)
                await asyncio.sleep((target - now).total_seconds())
                await fn()

        elif kind == "weekly":
            weekday, time_str = spec
            wd = self._weekday_num(weekday)
            hh, mm = self._parse_hm(time_str)
            while True:
                now = _dt.datetime.now()
                days_ahead = (wd - now.weekday()) % 7
                target = now.replace(hour=hh, minute=mm, second=0, microsecond=0) \
                    + _dt.timedelta(days=days_ahead)
                if target <= now:
                    target += _dt.timedelta(days=7)
                await asyncio.sleep((target - now).total_seconds())
                await fn()

        elif kind == "at":
            target = _dt.datetime.fromisoformat(str(spec))
            delay = (target - _dt.datetime.now()).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
            await fn()

        elif kind == "cron":
            try:
                from croniter import croniter
            except ImportError:
                return  # cron silently disabled without croniter
            itr = croniter(spec, _dt.datetime.now())
            while True:
                nxt = itr.get_next(_dt.datetime)
                await asyncio.sleep(max(0, (nxt - _dt.datetime.now()).total_seconds()))
                await fn()


# ─────────────────────────────────────────────────────────────
# BLOCK VISITORS — generate decorated async job functions
# ─────────────────────────────────────────────────────────────

def _job_name():
    _job_counter[0] += 1
    return f"_sched_job_{_job_counter[0]}"


def _emit_job(transpiler, deco_call, body):
    indent = "    " * transpiler._indent
    fname = _job_name()
    body_code = transpiler._block(body)
    return "\n".join([
        f"{indent}@__scheduler__.{deco_call}",
        f"{indent}async def {fname}():",
        body_code if body_code.strip() else f"{indent}    pass",
    ])


def _visit_every(transpiler, node):
    kw = node.kwargs
    parts = [f"{k}={kw[k].strip()}" for k in ("seconds", "minutes", "hours") if k in kw]
    if not parts and node.args:
        parts.append(f"seconds={node.args[0].strip()}")
    return _emit_job(transpiler, f"every({', '.join(parts)})", node.body)


def _visit_daily(transpiler, node):
    t = node.args[0].strip() if node.args else '"00:00"'
    if t[:1] not in ('"', "'"):
        t = repr(t)
    return _emit_job(transpiler, f"daily({t})", node.body)


def _visit_weekly(transpiler, node):
    day = node.args[0].strip().strip("\"'") if node.args else "monday"
    t = node.args[1].strip() if len(node.args) > 1 else '"00:00"'
    if t[:1] not in ('"', "'"):
        t = repr(t)
    return _emit_job(transpiler, f"weekly({day!r}, {t})", node.body)


def _visit_at(transpiler, node):
    when = node.args[0].strip() if node.args else '"1970-01-01 00:00"'
    if when[:1] not in ('"', "'"):
        when = repr(when)
    return _emit_job(transpiler, f"at({when})", node.body)


def _visit_cron(transpiler, node):
    expr = node.args[0].strip() if node.args else '"* * * * *"'
    if expr[:1] not in ('"', "'"):
        expr = repr(expr)
    return _emit_job(transpiler, f"cron({expr})", node.body)


# ─────────────────────────────────────────────────────────────
# PLUGIN ENTRY POINT
# ─────────────────────────────────────────────────────────────

def register(api):
    api.lib("schedule", None)
    api.lexer_hook(_preprocess)
    api.inject("__scheduler__", _CruhonScheduler())

    api.block_command("_sch_every",  _visit_every)
    api.block_command("_sch_daily",  _visit_daily)
    api.block_command("_sch_weekly", _visit_weekly)
    api.block_command("_sch_at",     _visit_at)
    api.block_command("_sch_cron",   _visit_cron)

    api.lib_call("schedule", "start", lambda a: "__scheduler__.start()")
    api.lib_call("schedule", "stop",  lambda a: "__scheduler__.stop()")
    api.lib_call("schedule", "count", lambda a: "__scheduler__.count()")
