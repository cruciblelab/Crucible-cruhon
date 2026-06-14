"""
cruhon/core/libs/traceback_.py
==============================
Exception & stack formatting for Cruhon — @traceback.*

Turn the currently-handled exception (or any exception object) into
readable text, and inspect the call stack.

━━━ CURRENT EXCEPTION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @traceback.format[]             → traceback of the exception being handled
  @traceback.print[]              → print that traceback to stderr

━━━ ANY EXCEPTION OBJECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @traceback.format_exception[e]  → full traceback string for exception e
  @traceback.message[e]           → "TypeName: message" one-liner for e

━━━ STACK ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @traceback.stack[]              → list of formatted stack frames
  @traceback.print_stack[]        → print current stack to stderr
  @traceback.extract[]            → StackSummary of the current call stack
  @traceback.frames[e]            → extracted frames (FrameSummary list) of e
  @traceback.format_frames[summary] → formatted lines from a StackSummary
"""
from ..registry import register_lib, register_lib_call

_TB = "__import__('traceback')"


def register():
    register_lib("traceback", None)

    # ── Current exception ─────────────────────────────────────
    register_lib_call("traceback", "format",
        lambda a: f"{_TB}.format_exc()")
    register_lib_call("traceback", "print",
        lambda a: f"{_TB}.print_exc()")

    # ── Any exception object ──────────────────────────────────
    register_lib_call("traceback", "format_exception",
        lambda a: (
            f"(lambda _e: ''.join({_TB}.format_exception(type(_e), _e, _e.__traceback__)))({a[0]})"
        ))
    register_lib_call("traceback", "message",
        lambda a: (
            f"(lambda _e: ''.join({_TB}.format_exception_only(type(_e), _e)).strip())({a[0]})"
        ))

    # ── Stack ─────────────────────────────────────────────────
    register_lib_call("traceback", "stack",
        lambda a: f"{_TB}.format_stack()")
    register_lib_call("traceback", "print_stack",
        lambda a: f"{_TB}.print_stack()")
    register_lib_call("traceback", "extract",
        lambda a: f"{_TB}.extract_stack()")
    register_lib_call("traceback", "frames",
        lambda a: f"(lambda _e: {_TB}.extract_tb(_e.__traceback__))({a[0]})")
    register_lib_call("traceback", "format_frames",
        lambda a: f"{_TB}.format_list({a[0]})")
