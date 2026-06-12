"""Operator stdlib wrappers for Cruhon — @operator.*"""
from ..registry import register_lib, register_lib_call

_OP = "__import__('operator')"


def register():
    register_lib("operator", "operator")

    # Key functions (commonly used with sorted/map/filter)
    register_lib_call("operator", "itemgetter",
        lambda a: f"{_OP}.itemgetter({', '.join(a)})")

    register_lib_call("operator", "attrgetter",
        lambda a: f"{_OP}.attrgetter({', '.join(a)})")

    register_lib_call("operator", "methodcaller",
        lambda a: f"{_OP}.methodcaller({', '.join(a)})")

    # Arithmetic
    register_lib_call("operator", "add",
        lambda a: f"{_OP}.add({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.add")

    register_lib_call("operator", "sub",
        lambda a: f"{_OP}.sub({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.sub")

    register_lib_call("operator", "mul",
        lambda a: f"{_OP}.mul({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.mul")

    register_lib_call("operator", "truediv",
        lambda a: f"{_OP}.truediv({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.truediv")

    register_lib_call("operator", "floordiv",
        lambda a: f"{_OP}.floordiv({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.floordiv")

    register_lib_call("operator", "mod",
        lambda a: f"{_OP}.mod({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.mod")

    register_lib_call("operator", "pow",
        lambda a: f"{_OP}.pow({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.pow")

    register_lib_call("operator", "neg",
        lambda a: f"{_OP}.neg({a[0]})")

    register_lib_call("operator", "pos",
        lambda a: f"{_OP}.pos({a[0]})")

    register_lib_call("operator", "abs",
        lambda a: f"{_OP}.abs({a[0]})")

    # Comparison
    register_lib_call("operator", "eq",
        lambda a: f"{_OP}.eq({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.eq")

    register_lib_call("operator", "ne",
        lambda a: f"{_OP}.ne({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.ne")

    register_lib_call("operator", "lt",
        lambda a: f"{_OP}.lt({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.lt")

    register_lib_call("operator", "le",
        lambda a: f"{_OP}.le({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.le")

    register_lib_call("operator", "gt",
        lambda a: f"{_OP}.gt({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.gt")

    register_lib_call("operator", "ge",
        lambda a: f"{_OP}.ge({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.ge")

    # Logical
    register_lib_call("operator", "not_",
        lambda a: f"{_OP}.not_({a[0]})")

    register_lib_call("operator", "and_",
        lambda a: f"{_OP}.and_({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.and_")

    register_lib_call("operator", "or_",
        lambda a: f"{_OP}.or_({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.or_")

    register_lib_call("operator", "xor",
        lambda a: f"{_OP}.xor({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.xor")

    # Container
    register_lib_call("operator", "getitem",
        lambda a: f"{_OP}.getitem({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.getitem")

    register_lib_call("operator", "setitem",
        lambda a: f"{_OP}.setitem({a[0]}, {a[1]}, {a[2]})" if len(a) > 2 else f"{_OP}.setitem")

    register_lib_call("operator", "delitem",
        lambda a: f"{_OP}.delitem({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.delitem")

    register_lib_call("operator", "contains",
        lambda a: f"{_OP}.contains({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.contains")

    register_lib_call("operator", "length_hint",
        lambda a: f"{_OP}.length_hint({a[0]})")

    register_lib_call("operator", "concat",
        lambda a: f"{_OP}.concat({a[0]}, {a[1]})" if len(a) > 1 else f"{_OP}.concat")
