"""Time stdlib wrappers for Cruhon."""
from ..registry import register_lib, register_lib_call


def register():
    register_lib("time", "time")

    register_lib_call("time", "now",
        lambda args: "__import__('datetime').datetime.now()")

    register_lib_call("time", "date",
        lambda args: "__import__('datetime').date.today()")

    register_lib_call("time", "timestamp",
        lambda args: "__import__('time').time()")

    register_lib_call("time", "sleep",
        lambda args: (
            f"__import__('time').sleep({args[0]})"
            if args else "__import__('time').sleep(0)"
        ))

    register_lib_call("time", "format",
        lambda args: (
            f"__import__('datetime').datetime.now().strftime({args[0]})"
            if args else "__import__('datetime').datetime.now().strftime('%Y-%m-%d')"
        ))
