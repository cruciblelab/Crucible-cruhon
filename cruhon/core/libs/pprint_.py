"""Pprint stdlib wrappers for Cruhon — @pprint.*"""
from ..registry import register_lib, register_lib_call

_PP = "__import__('pprint')"


def register():
    register_lib("pprint", "pprint")

    register_lib_call("pprint", "print",
        lambda a: (
            f"{_PP}.pprint({a[0]}, indent={a[1]}, width={a[2]})" if len(a) > 2 else
            f"{_PP}.pprint({a[0]}, indent={a[1]})" if len(a) > 1 else
            f"{_PP}.pprint({a[0] if a else 'None'})"
        ))

    register_lib_call("pprint", "format",
        lambda a: (
            f"{_PP}.pformat({a[0]}, indent={a[1]}, width={a[2]})" if len(a) > 2 else
            f"{_PP}.pformat({a[0]}, indent={a[1]})" if len(a) > 1 else
            f"{_PP}.pformat({a[0] if a else 'None'})"
        ))

    register_lib_call("pprint", "isreadable",
        lambda a: f"{_PP}.isreadable({a[0]})")

    register_lib_call("pprint", "isrecursive",
        lambda a: f"{_PP}.isrecursive({a[0]})")

    register_lib_call("pprint", "saferepr",
        lambda a: f"{_PP}.saferepr({a[0]})")

    register_lib_call("pprint", "PrettyPrinter",
        lambda a: (
            f"{_PP}.PrettyPrinter(indent={a[0]}, width={a[1]})" if len(a) > 1 else
            f"{_PP}.PrettyPrinter(indent={a[0]})" if a else
            f"{_PP}.PrettyPrinter()"
        ))

    register_lib_call("pprint", "pp",
        lambda a: f"{_PP}.pp({a[0] if a else 'None'})")
