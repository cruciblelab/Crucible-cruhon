"""Typing stdlib wrappers for Cruhon — @typing.*"""
from ..registry import register_lib, register_lib_call

_TY = "__import__('typing')"


def register():
    register_lib("typing", "typing")

    register_lib_call("typing", "Optional",
        lambda a: f"{_TY}.Optional[{a[0]}]" if a else f"{_TY}.Optional")

    register_lib_call("typing", "Union",
        lambda a: f"{_TY}.Union[{', '.join(a)}]" if a else f"{_TY}.Union")

    register_lib_call("typing", "List",
        lambda a: f"{_TY}.List[{a[0]}]" if a else f"{_TY}.List")

    register_lib_call("typing", "Dict",
        lambda a: f"{_TY}.Dict[{a[0]}, {a[1]}]" if len(a) > 1 else f"{_TY}.Dict")

    register_lib_call("typing", "Tuple",
        lambda a: f"{_TY}.Tuple[{', '.join(a)}]" if a else f"{_TY}.Tuple")

    register_lib_call("typing", "Set",
        lambda a: f"{_TY}.Set[{a[0]}]" if a else f"{_TY}.Set")

    register_lib_call("typing", "Any",
        lambda a: f"{_TY}.Any")

    register_lib_call("typing", "Callable",
        lambda a: f"{_TY}.Callable[{', '.join(a)}]" if a else f"{_TY}.Callable")

    register_lib_call("typing", "cast",
        lambda a: f"{_TY}.cast({a[0]}, {a[1]})" if len(a) > 1 else f"{_TY}.cast({a[0]}, None)")

    register_lib_call("typing", "TypeVar",
        lambda a: f"{_TY}.TypeVar({a[0]}{', ' + ', '.join(a[1:]) if len(a)>1 else ''})")

    register_lib_call("typing", "TypeAlias",
        lambda a: f"{_TY}.TypeAlias")

    register_lib_call("typing", "Final",
        lambda a: f"{_TY}.Final[{a[0]}]" if a else f"{_TY}.Final")

    register_lib_call("typing", "Literal",
        lambda a: f"{_TY}.Literal[{', '.join(a)}]" if a else f"{_TY}.Literal")

    register_lib_call("typing", "ClassVar",
        lambda a: f"{_TY}.ClassVar[{a[0]}]" if a else f"{_TY}.ClassVar")

    register_lib_call("typing", "Protocol",
        lambda a: f"{_TY}.Protocol")

    register_lib_call("typing", "runtime_checkable",
        lambda a: f"{_TY}.runtime_checkable({a[0]})")

    register_lib_call("typing", "overload",
        lambda a: f"{_TY}.overload")

    register_lib_call("typing", "TYPE_CHECKING",
        lambda a: f"{_TY}.TYPE_CHECKING")

    register_lib_call("typing", "get_type_hints",
        lambda a: f"{_TY}.get_type_hints({a[0]})")

    register_lib_call("typing", "NamedTuple",
        lambda a: f"{_TY}.NamedTuple")
