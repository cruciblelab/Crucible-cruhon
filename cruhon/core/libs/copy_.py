"""Copy stdlib wrappers for Cruhon — @copy.*"""
from ..registry import register_lib, register_lib_call

_CP = "__import__('copy')"


def register():
    register_lib("copy", "copy")

    register_lib_call("copy", "copy",
        lambda a: f"{_CP}.copy({a[0]})")

    register_lib_call("copy", "deepcopy",
        lambda a: f"{_CP}.deepcopy({a[0]})")

    register_lib_call("copy", "replace",
        lambda a: f"{_CP}.replace({a[0]}, {', '.join(a[1:])})" if len(a) > 1 else f"{_CP}.copy({a[0]})")
