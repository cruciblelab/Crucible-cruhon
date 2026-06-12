"""Functools stdlib wrappers for Cruhon — @functools.*"""
from ..registry import register_lib, register_lib_call

_F = "__import__('functools')"


def register():
    register_lib("functools", "functools")

    register_lib_call("functools", "reduce",
        lambda a: f"{_F}.reduce({a[0]}, {a[1]}{', ' + a[2] if len(a)>2 else ''})")

    register_lib_call("functools", "partial",
        lambda a: f"{_F}.partial({', '.join(a)})")

    register_lib_call("functools", "lru_cache",
        lambda a: f"{_F}.lru_cache(maxsize={a[0] if a else 128})")

    register_lib_call("functools", "cache",
        lambda a: f"{_F}.cache")

    register_lib_call("functools", "cached_property",
        lambda a: f"{_F}.cached_property({a[0]})")

    register_lib_call("functools", "wraps",
        lambda a: f"{_F}.wraps({a[0]})")

    register_lib_call("functools", "total_ordering",
        lambda a: f"{_F}.total_ordering")

    register_lib_call("functools", "singledispatch",
        lambda a: f"{_F}.singledispatch({a[0]})")

    register_lib_call("functools", "singledispatchmethod",
        lambda a: f"{_F}.singledispatchmethod({a[0]})")

    register_lib_call("functools", "update_wrapper",
        lambda a: f"{_F}.update_wrapper({a[0]}, {a[1]})" if len(a) > 1 else f"{_F}.update_wrapper({a[0]}, {a[0]})")

    register_lib_call("functools", "cmp_to_key",
        lambda a: f"{_F}.cmp_to_key({a[0]})")
