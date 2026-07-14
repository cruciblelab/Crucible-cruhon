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

    # ── Previously documented but never actually registered ────
    # (README/library.md listed these under @math.* — implemented for real
    # rather than walking the docs back, since they're genuinely useful.)

    register_lib_call("math", "clamp",
        lambda args: f"max({args[1]}, min({args[0]}, {args[2]}))")

    register_lib_call("math", "lerp",
        lambda args: f"({args[0]} + ({args[1]} - {args[0]}) * {args[2]})")

    register_lib_call("math", "sign",
        lambda args: f"((({args[0]}) > 0) - (({args[0]}) < 0))")

    register_lib_call("math", "hypot",
        lambda args: f"__import__('math').hypot({', '.join(args)})")

    register_lib_call("math", "dist",
        lambda args: f"__import__('math').dist({args[0]}, {args[1]})")

    register_lib_call("math", "gcd",
        lambda args: f"__import__('math').gcd({', '.join(args)})")

    register_lib_call("math", "lcm",
        lambda args: f"__import__('math').lcm({', '.join(args)})")

    register_lib_call("math", "factorial",
        lambda args: f"__import__('math').factorial({args[0]})")

    register_lib_call("math", "comb",
        lambda args: f"__import__('math').comb({args[0]}, {args[1]})")

    register_lib_call("math", "perm",
        lambda args: (
            f"__import__('math').perm({args[0]}, {args[1]})" if len(args) > 1
            else f"__import__('math').perm({args[0]})"
        ))

    register_lib_call("math", "prod",
        lambda args: f"__import__('math').prod({args[0]})")

    register_lib_call("math", "degrees",
        lambda args: f"__import__('math').degrees({args[0]})")

    register_lib_call("math", "radians",
        lambda args: f"__import__('math').radians({args[0]})")

    register_lib_call("math", "log2",
        lambda args: f"__import__('math').log2({args[0]})")

    register_lib_call("math", "log10",
        lambda args: f"__import__('math').log10({args[0]})")

    register_lib_call("math", "exp",
        lambda args: f"__import__('math').exp({args[0]})")

    register_lib_call("math", "sin",
        lambda args: f"__import__('math').sin({args[0]})")

    register_lib_call("math", "cos",
        lambda args: f"__import__('math').cos({args[0]})")

    register_lib_call("math", "tan",
        lambda args: f"__import__('math').tan({args[0]})")

    register_lib_call("math", "asin",
        lambda args: f"__import__('math').asin({args[0]})")

    register_lib_call("math", "acos",
        lambda args: f"__import__('math').acos({args[0]})")

    register_lib_call("math", "atan",
        lambda args: f"__import__('math').atan({args[0]})")

    register_lib_call("math", "atan2",
        lambda args: f"__import__('math').atan2({args[0]}, {args[1]})")

    register_lib_call("math", "isclose",
        lambda args: f"__import__('math').isclose({args[0]}, {args[1]})")

    register_lib_call("math", "isfinite",
        lambda args: f"__import__('math').isfinite({args[0]})")

    register_lib_call("math", "isinf",
        lambda args: f"__import__('math').isinf({args[0]})")

    register_lib_call("math", "isnan",
        lambda args: f"__import__('math').isnan({args[0]})")

    register_lib_call("math", "e",
        lambda args: "__import__('math').e")

    register_lib_call("math", "tau",
        lambda args: "__import__('math').tau")

    register_lib_call("math", "inf",
        lambda args: "__import__('math').inf")

    register_lib_call("math", "nan",
        lambda args: "__import__('math').nan")

    register_lib_call("math", "min",
        lambda args: f"min({args[0]})")

    register_lib_call("math", "max",
        lambda args: f"max({args[0]})")

    register_lib_call("math", "sum",
        lambda args: f"sum({args[0]})")
