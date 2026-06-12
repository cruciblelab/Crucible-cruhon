"""Dataclasses stdlib wrappers for Cruhon — @dataclasses.*"""
from ..registry import register_lib, register_lib_call

_DC = "__import__('dataclasses')"


def register():
    register_lib("dataclasses", "dataclasses")

    register_lib_call("dataclasses", "dataclass",
        lambda a: f"{_DC}.dataclass")

    register_lib_call("dataclasses", "field",
        lambda a: f"{_DC}.field({', '.join(a)})")

    register_lib_call("dataclasses", "asdict",
        lambda a: f"{_DC}.asdict({a[0]})")

    register_lib_call("dataclasses", "astuple",
        lambda a: f"{_DC}.astuple({a[0]})")

    register_lib_call("dataclasses", "fields",
        lambda a: f"{_DC}.fields({a[0]})")

    register_lib_call("dataclasses", "replace",
        lambda a: f"{_DC}.replace({a[0]}, {', '.join(a[1:])})" if len(a) > 1 else f"{_DC}.replace({a[0]})")

    register_lib_call("dataclasses", "is_dataclass",
        lambda a: f"{_DC}.is_dataclass({a[0]})")

    register_lib_call("dataclasses", "make_dataclass",
        lambda a: f"{_DC}.make_dataclass({a[0]}, {a[1]})" if len(a) > 1 else f"{_DC}.make_dataclass({a[0]}, [])")

    register_lib_call("dataclasses", "FrozenInstanceError",
        lambda a: f"{_DC}.FrozenInstanceError")

    register_lib_call("dataclasses", "InitVar",
        lambda a: f"{_DC}.InitVar")

    register_lib_call("dataclasses", "KW_ONLY",
        lambda a: f"{_DC}.KW_ONLY")
