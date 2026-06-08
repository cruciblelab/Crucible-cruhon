"""Math stdlib wrappers for Cruhon."""
from ..registry import register_lib, register_lib_call


def register():
    register_lib("math", "math")

    register_lib_call("math", "sqrt",
        lambda args: f"__import__('math').sqrt({args[0]})")

    register_lib_call("math", "floor",
        lambda args: f"__import__('math').floor({args[0]})")

    register_lib_call("math", "ceil",
        lambda args: f"__import__('math').ceil({args[0]})")

    register_lib_call("math", "abs",
        lambda args: f"abs({args[0]})")

    register_lib_call("math", "pow",
        lambda args: (
            f"__import__('math').pow({args[0]}, {args[1]})"
            if len(args) > 1 else f"__import__('math').pow({args[0]}, 2)"
        ))

    register_lib_call("math", "log",
        lambda args: f"__import__('math').log({args[0]})")

    register_lib_call("math", "round",
        lambda args: (
            f"round({args[0]}, {args[1]})"
            if len(args) > 1 else f"round({args[0]})"
        ))

    register_lib_call("math", "pi",
        lambda args: "__import__('math').pi")

    register_lib_call("math", "random",
        lambda args: (
            f"__import__('random').randint({args[0]}, {args[1]})"
            if len(args) > 1 else "__import__('random').randint(0, 100)"
        ))

    register_lib_call("math", "rand",
        lambda args: "__import__('random').random()")
