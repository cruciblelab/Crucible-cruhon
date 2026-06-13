"""
cruhon/core/libs/profile_.py
============================
Deterministic profiling for Cruhon — @profile.*

Measure where time goes inside a callable using cProfile.

━━━ PROFILE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @profile.run[fn]                → pstats.Stats after profiling fn()
  @profile.calls[fn]             → total number of function calls made
  @profile.time[fn]              → total time spent (seconds)
  @profile.print[fn]             → run fn() and print sorted stats to stdout
  @profile.print[fn; n]          → print only the top n lines
  @profile.dump[fn; path]        → run fn() and save raw stats to a file
"""
from ..registry import register_lib, register_lib_call

# enable a fresh Profiler, run _f(), disable, then hand a pstats.Stats back
_PROFILE = (
    "(lambda _f, _after: (lambda _p: (_p.enable(), _f(), _p.disable(), "
    "_after(__import__('pstats').Stats(_p)))[3])(__import__('cProfile').Profile()))"
)


def register():
    register_lib("profile", None)

    register_lib_call("profile", "run",
        lambda a: f"{_PROFILE}({a[0]}, lambda _s: _s)")
    register_lib_call("profile", "calls",
        lambda a: f"{_PROFILE}({a[0]}, lambda _s: _s.total_calls)")
    register_lib_call("profile", "time",
        lambda a: f"{_PROFILE}({a[0]}, lambda _s: _s.total_tt)")
    register_lib_call("profile", "print",
        lambda a: (
            f"{_PROFILE}({a[0]}, lambda _s: (_s.sort_stats('cumulative'), _s.print_stats({a[1]}))[1])"
            if len(a) > 1 else
            f"{_PROFILE}({a[0]}, lambda _s: (_s.sort_stats('cumulative'), _s.print_stats())[1])"
        ))
    register_lib_call("profile", "dump",
        lambda a: f"{_PROFILE}({a[0]}, lambda _s: _s.dump_stats({a[1]}))")
