"""
cruhon/core/libs/resource_.py
=============================
Process resource usage & limits for Cruhon — @resource.*  (Unix only)

Measure CPU time and memory used by this process, and read/set resource
limits.

━━━ USAGE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @resource.usage[]               → full getrusage() struct for this process
  @resource.max_rss[]             → peak memory (ru_maxrss; KB on Linux)
  @resource.user_time[]           → CPU time spent in user mode (seconds)
  @resource.sys_time[]            → CPU time spent in kernel mode (seconds)

━━━ LIMITS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @resource.limit[name]           → (soft, hard) limit for "NOFILE" etc.
  @resource.set_limit[name; soft; hard] → set a limit
  @resource.page_size[]           → system memory page size in bytes
"""
from ..registry import register_lib, register_lib_call

_RS = "__import__('resource')"


def register():
    register_lib("resource", None)

    # ── Usage ─────────────────────────────────────────────────
    register_lib_call("resource", "usage",
        lambda a: f"{_RS}.getrusage({_RS}.RUSAGE_SELF)")
    register_lib_call("resource", "max_rss",
        lambda a: f"{_RS}.getrusage({_RS}.RUSAGE_SELF).ru_maxrss")
    register_lib_call("resource", "user_time",
        lambda a: f"{_RS}.getrusage({_RS}.RUSAGE_SELF).ru_utime")
    register_lib_call("resource", "sys_time",
        lambda a: f"{_RS}.getrusage({_RS}.RUSAGE_SELF).ru_stime")

    # ── Limits ────────────────────────────────────────────────
    register_lib_call("resource", "limit",
        lambda a: f"{_RS}.getrlimit(getattr({_RS}, 'RLIMIT_' + {a[0]}))")
    register_lib_call("resource", "set_limit",
        lambda a: f"{_RS}.setrlimit(getattr({_RS}, 'RLIMIT_' + {a[0]}), ({a[1]}, {a[2]}))")
    register_lib_call("resource", "page_size",
        lambda a: f"{_RS}.getpagesize()")
