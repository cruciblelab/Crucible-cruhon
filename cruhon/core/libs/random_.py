"""Random number / sampling wrappers for Cruhon — @random.*"""
from ..registry import register_lib, register_lib_call

_R = "__import__('random')"


def register():
    register_lib("random", "random")

    register_lib_call("random", "random",
        lambda a: f"{_R}.random()")

    register_lib_call("random", "randint",
        lambda a: f"{_R}.randint({a[0]}, {a[1]})" if len(a) > 1 else f"{_R}.randint(0, 100)")

    register_lib_call("random", "randrange",
        lambda a: (
            f"{_R}.randrange({a[0]}, {a[1]}, {a[2]})" if len(a) > 2 else
            f"{_R}.randrange({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_R}.randrange({a[0]})"
        ))

    register_lib_call("random", "uniform",
        lambda a: f"{_R}.uniform({a[0]}, {a[1]})" if len(a) > 1 else f"{_R}.uniform(0.0, 1.0)")

    register_lib_call("random", "choice",
        lambda a: f"{_R}.choice({a[0]})")

    register_lib_call("random", "choices",
        lambda a: (
            f"{_R}.choices({a[0]}, k={a[1]})" if len(a) > 1 else
            f"{_R}.choices({a[0]})"
        ))

    register_lib_call("random", "sample",
        lambda a: f"{_R}.sample({a[0]}, {a[1]})" if len(a) > 1 else f"{_R}.sample({a[0]}, 1)")

    register_lib_call("random", "shuffle",
        lambda a: f"{_R}.shuffle({a[0]})")

    register_lib_call("random", "seed",
        lambda a: f"{_R}.seed({a[0] if a else 'None'})")

    register_lib_call("random", "gauss",
        lambda a: f"{_R}.gauss({a[0]}, {a[1]})" if len(a) > 1 else f"{_R}.gauss(0, 1)")

    register_lib_call("random", "triangular",
        lambda a: (
            f"{_R}.triangular({a[0]}, {a[1]}, {a[2]})" if len(a) > 2 else
            f"{_R}.triangular({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_R}.triangular()"
        ))

    register_lib_call("random", "betavariate",
        lambda a: f"{_R}.betavariate({a[0]}, {a[1]})" if len(a) > 1 else f"{_R}.betavariate(1, 1)")

    register_lib_call("random", "expovariate",
        lambda a: f"{_R}.expovariate({a[0] if a else 1})")

    register_lib_call("random", "getstate",
        lambda a: f"{_R}.getstate()")

    register_lib_call("random", "setstate",
        lambda a: f"{_R}.setstate({a[0]})")
