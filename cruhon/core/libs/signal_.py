"""
cruhon/core/libs/signal_.py
===========================
OS signal helpers for Cruhon — @signal.*

Look up signal numbers/names and send or schedule signals.

━━━ NAME ↔ NUMBER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @signal.number[name]            → numeric value of "SIGINT" etc.
  @signal.name[num]               → "SIGINT" for a number
  @signal.describe[num]           → human description (strsignal)
  @signal.valid[]                 → set of valid signal numbers

━━━ HANDLERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @signal.get[num]                → current handler for a signal
  @signal.on[num; fn]             → install fn as handler, returns old handler
  @signal.ignore[num]             → ignore a signal (SIG_IGN)
  @signal.default[num]            → restore default handler (SIG_DFL)

━━━ SEND / SCHEDULE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @signal.send[num]               → raise a signal in this process
  @signal.alarm[seconds]          → schedule SIGALRM after N seconds (Unix)
  @signal.set_timer[seconds]      → start a real-time interval timer (SIGALRM)
  @signal.get_timer[]             → (value, interval) of the real-time timer
  @signal.pause[]                 → block until a signal is received (Unix)
"""
from ..registry import register_lib, register_lib_call

_SG = "__import__('signal')"


def register():
    register_lib("signal", None)

    # ── Name ↔ Number ─────────────────────────────────────────
    register_lib_call("signal", "number",
        lambda a: f"int({_SG}.Signals[{a[0]}])")
    register_lib_call("signal", "name",
        lambda a: f"{_SG}.Signals({a[0]}).name")
    register_lib_call("signal", "describe",
        lambda a: f"{_SG}.strsignal({a[0]})")
    register_lib_call("signal", "valid",
        lambda a: f"{_SG}.valid_signals()")

    # ── Handlers ──────────────────────────────────────────────
    register_lib_call("signal", "get",
        lambda a: f"{_SG}.getsignal({a[0]})")
    register_lib_call("signal", "on",
        lambda a: f"{_SG}.signal({a[0]}, {a[1]})")
    register_lib_call("signal", "ignore",
        lambda a: f"{_SG}.signal({a[0]}, {_SG}.SIG_IGN)")
    register_lib_call("signal", "default",
        lambda a: f"{_SG}.signal({a[0]}, {_SG}.SIG_DFL)")

    # ── Send / Schedule ───────────────────────────────────────
    register_lib_call("signal", "send",
        lambda a: f"{_SG}.raise_signal({a[0]})")
    register_lib_call("signal", "alarm",
        lambda a: f"{_SG}.alarm({a[0]})")
    register_lib_call("signal", "set_timer",
        lambda a: f"{_SG}.setitimer({_SG}.ITIMER_REAL, {a[0]})")
    register_lib_call("signal", "get_timer",
        lambda a: f"{_SG}.getitimer({_SG}.ITIMER_REAL)")
    register_lib_call("signal", "pause",
        lambda a: f"{_SG}.pause()")
