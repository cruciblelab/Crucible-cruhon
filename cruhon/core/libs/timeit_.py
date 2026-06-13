"""
cruhon/core/libs/timeit_.py
===========================
Micro-benchmarking for Cruhon — @timeit.*

Time how long a callable takes to run, averaged over many iterations.

━━━ TIMING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @timeit.run[fn]                 → total seconds for 1,000,000 calls of fn
  @timeit.run[fn; number]         → total seconds for `number` calls
  @timeit.each[fn; number]        → average seconds per single call
  @timeit.repeat[fn; reps; number]→ list of timings across `reps` runs
  @timeit.best[fn]                → best of 5×100,000 runs (seconds)
  @timeit.auto[fn]                → (loops, seconds) chosen automatically
"""
from ..registry import register_lib, register_lib_call

_TI = "__import__('timeit')"


def register():
    register_lib("timeit", None)

    register_lib_call("timeit", "run",
        lambda a: (
            f"{_TI}.timeit({a[0]}, number={a[1]})" if len(a) > 1 else
            f"{_TI}.timeit({a[0]}, number=1000000)"
        ))
    register_lib_call("timeit", "each",
        lambda a: f"({_TI}.timeit({a[0]}, number={a[1]}) / {a[1]})")
    register_lib_call("timeit", "repeat",
        lambda a: f"{_TI}.repeat({a[0]}, repeat={a[1]}, number={a[2]})")
    register_lib_call("timeit", "best",
        lambda a: f"min({_TI}.repeat({a[0]}, repeat=5, number=100000))")
    register_lib_call("timeit", "auto",
        lambda a: f"{_TI}.Timer({a[0]}).autorange()")
