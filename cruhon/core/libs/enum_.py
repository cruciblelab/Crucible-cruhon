"""Enum stdlib wrappers for Cruhon — @enum.*"""
from ..registry import register_lib, register_lib_call

_EN = "__import__('enum')"


def register():
    register_lib("enum", "enum")

    # Bare (no args) → the class itself, for type annotations / isinstance
    # checks. With args → Python's own functional-constructor behavior
    # (enum.Enum("Color", "RED GREEN BLUE") really does build a new enum
    # when called) — matching that instead of silently discarding the
    # args avoids a confusing AttributeError far from the real cause.
    register_lib_call("enum", "Enum",
        lambda a: f"{_EN}.Enum({a[0]}, {a[1]})" if len(a) > 1 else f"{_EN}.Enum")

    register_lib_call("enum", "IntEnum",
        lambda a: f"{_EN}.IntEnum({a[0]}, {a[1]})" if len(a) > 1 else f"{_EN}.IntEnum")

    register_lib_call("enum", "StrEnum",
        lambda a: f"{_EN}.StrEnum({a[0]}, {a[1]})" if len(a) > 1 else f"{_EN}.StrEnum")

    register_lib_call("enum", "Flag",
        lambda a: f"{_EN}.Flag({a[0]}, {a[1]})" if len(a) > 1 else f"{_EN}.Flag")

    register_lib_call("enum", "IntFlag",
        lambda a: f"{_EN}.IntFlag({a[0]}, {a[1]})" if len(a) > 1 else f"{_EN}.IntFlag")

    register_lib_call("enum", "auto",
        lambda a: f"{_EN}.auto()")

    register_lib_call("enum", "create",
        lambda a: f"{_EN}.Enum({a[0]}, {a[1]})" if len(a) > 1 else f"{_EN}.Enum({a[0]}, [])")

    register_lib_call("enum", "unique",
        lambda a: f"{_EN}.unique({a[0]})")

    register_lib_call("enum", "list",
        lambda a: f"list({a[0]})")

    register_lib_call("enum", "names",
        lambda a: f"[m.name for m in {a[0]}]")

    register_lib_call("enum", "values",
        lambda a: f"[m.value for m in {a[0]}]")

    register_lib_call("enum", "members",
        lambda a: f"list({a[0]}.__members__.items())")
