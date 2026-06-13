"""
cruhon/core/libs/atexit_.py
===========================
Exit-time callbacks for Cruhon — @atexit.*

Register functions to run automatically when the interpreter shuts down.

━━━ REGISTER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @atexit.register[fn]            → run fn at exit (returns fn)
  @atexit.unregister[fn]          → cancel a previously-registered fn
  @atexit.run[]                   → run all registered callbacks now
"""
from ..registry import register_lib, register_lib_call

_AE = "__import__('atexit')"


def register():
    register_lib("atexit", None)

    register_lib_call("atexit", "register",
        lambda a: f"{_AE}.register({a[0]})")
    register_lib_call("atexit", "unregister",
        lambda a: f"{_AE}.unregister({a[0]})")
    register_lib_call("atexit", "run",
        lambda a: f"{_AE}._run_exitfuncs()")
