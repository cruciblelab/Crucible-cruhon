"""Itertools stdlib wrappers for Cruhon — @itertools.*"""
from ..registry import register_lib, register_lib_call

_IT = "__import__('itertools')"


def register():
    register_lib("itertools", "itertools")

    register_lib_call("itertools", "chain",
        lambda a: f"{_IT}.chain({', '.join(a)})")

    register_lib_call("itertools", "chain_from_iterable",
        lambda a: f"{_IT}.chain.from_iterable({a[0]})")

    register_lib_call("itertools", "cycle",
        lambda a: f"{_IT}.cycle({a[0]})")

    register_lib_call("itertools", "repeat",
        lambda a: f"{_IT}.repeat({a[0]}, {a[1]})" if len(a) > 1 else f"{_IT}.repeat({a[0]})")

    register_lib_call("itertools", "count",
        lambda a: (
            f"{_IT}.count({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_IT}.count({a[0]})" if a else
            f"{_IT}.count()"
        ))

    register_lib_call("itertools", "product",
        lambda a: (
            f"{_IT}.product({', '.join(a[:-1])}, repeat={a[-1]})"
            if len(a) > 1 and a[-1].startswith('repeat=') else
            f"{_IT}.product({', '.join(a)})"
        ))

    register_lib_call("itertools", "permutations",
        lambda a: f"{_IT}.permutations({a[0]}, {a[1]})" if len(a) > 1 else f"{_IT}.permutations({a[0]})")

    register_lib_call("itertools", "combinations",
        lambda a: f"{_IT}.combinations({a[0]}, {a[1]})" if len(a) > 1 else f"{_IT}.combinations({a[0]}, 2)")

    register_lib_call("itertools", "combinations_with_replacement",
        lambda a: f"{_IT}.combinations_with_replacement({a[0]}, {a[1]})" if len(a) > 1 else f"{_IT}.combinations_with_replacement({a[0]}, 2)")

    register_lib_call("itertools", "zip_longest",
        lambda a: (
            f"{_IT}.zip_longest({', '.join(a[:-1])}, fillvalue={a[-1]})"
            if len(a) > 1 and a[-1].startswith('fillvalue=') else
            f"{_IT}.zip_longest({', '.join(a)})"
        ))

    register_lib_call("itertools", "groupby",
        lambda a: f"{_IT}.groupby({a[0]}, key={a[1]})" if len(a) > 1 else f"{_IT}.groupby({a[0]})")

    register_lib_call("itertools", "accumulate",
        lambda a: f"{_IT}.accumulate({a[0]}, {a[1]})" if len(a) > 1 else f"{_IT}.accumulate({a[0]})")

    register_lib_call("itertools", "takewhile",
        lambda a: f"{_IT}.takewhile({a[0]}, {a[1]})" if len(a) > 1 else f"{_IT}.takewhile(bool, {a[0]})")

    register_lib_call("itertools", "dropwhile",
        lambda a: f"{_IT}.dropwhile({a[0]}, {a[1]})" if len(a) > 1 else f"{_IT}.dropwhile(bool, {a[0]})")

    register_lib_call("itertools", "islice",
        lambda a: (
            f"{_IT}.islice({a[0]}, {a[1]}, {a[2]}, {a[3]})" if len(a) > 3 else
            f"{_IT}.islice({a[0]}, {a[1]}, {a[2]})" if len(a) > 2 else
            f"{_IT}.islice({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_IT}.islice({a[0]}, None)"
        ))

    register_lib_call("itertools", "starmap",
        lambda a: f"{_IT}.starmap({a[0]}, {a[1]})" if len(a) > 1 else f"{_IT}.starmap(lambda x: x, {a[0]})")

    register_lib_call("itertools", "filterfalse",
        lambda a: f"{_IT}.filterfalse({a[0]}, {a[1]})" if len(a) > 1 else f"{_IT}.filterfalse(None, {a[0]})")

    register_lib_call("itertools", "compress",
        lambda a: f"{_IT}.compress({a[0]}, {a[1]})" if len(a) > 1 else f"{_IT}.compress({a[0]}, [])")

    register_lib_call("itertools", "flatten",
        lambda a: f"list({_IT}.chain.from_iterable({a[0]}))")

    register_lib_call("itertools", "pairwise",
        lambda a: f"{_IT}.pairwise({a[0]})")

    register_lib_call("itertools", "tee",
        lambda a: f"{_IT}.tee({a[0]}, {a[1] if len(a)>1 else 2})")
