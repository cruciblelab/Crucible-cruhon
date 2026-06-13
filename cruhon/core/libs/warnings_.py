"""
cruhon/core/libs/warnings_.py
=============================
Warning control for Cruhon — @warnings.*

Emit warnings and control how they are filtered.

━━━ EMIT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @warnings.warn[msg]             → emit a UserWarning
  @warnings.warn[msg; category]   → emit with a specific warning class
  @warnings.deprecated[msg]       → emit a DeprecationWarning

━━━ FILTER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @warnings.ignore[]              → suppress all warnings
  @warnings.once[]                → show each warning only once
  @warnings.always[]              → always show warnings
  @warnings.error[]               → turn warnings into exceptions
  @warnings.filter[action]        → simplefilter with a custom action
  @warnings.reset[]               → reset filters to default
"""
from ..registry import register_lib, register_lib_call

_WN = "__import__('warnings')"


def register():
    register_lib("warnings", None)

    # ── Emit ──────────────────────────────────────────────────
    register_lib_call("warnings", "warn",
        lambda a: (
            f"{_WN}.warn({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_WN}.warn({a[0]})"
        ))
    register_lib_call("warnings", "deprecated",
        lambda a: f"{_WN}.warn({a[0]}, DeprecationWarning)")

    # ── Filter ────────────────────────────────────────────────
    register_lib_call("warnings", "ignore",
        lambda a: f"{_WN}.simplefilter('ignore')")
    register_lib_call("warnings", "once",
        lambda a: f"{_WN}.simplefilter('once')")
    register_lib_call("warnings", "always",
        lambda a: f"{_WN}.simplefilter('always')")
    register_lib_call("warnings", "error",
        lambda a: f"{_WN}.simplefilter('error')")
    register_lib_call("warnings", "filter",
        lambda a: f"{_WN}.simplefilter({a[0]})")
    register_lib_call("warnings", "reset",
        lambda a: f"{_WN}.resetwarnings()")
