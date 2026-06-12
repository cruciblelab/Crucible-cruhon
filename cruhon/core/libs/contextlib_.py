"""Contextlib stdlib wrappers for Cruhon — @contextlib.*"""
from ..registry import register_lib, register_lib_call

_CL = "__import__('contextlib')"


def register():
    register_lib("contextlib", "contextlib")

    register_lib_call("contextlib", "contextmanager",
        lambda a: f"{_CL}.contextmanager({a[0]})")

    register_lib_call("contextlib", "suppress",
        lambda a: f"{_CL}.suppress({', '.join(a)})")

    register_lib_call("contextlib", "nullcontext",
        lambda a: f"{_CL}.nullcontext({a[0] if a else ''})")

    register_lib_call("contextlib", "redirect_stdout",
        lambda a: f"{_CL}.redirect_stdout({a[0]})")

    register_lib_call("contextlib", "redirect_stderr",
        lambda a: f"{_CL}.redirect_stderr({a[0]})")

    register_lib_call("contextlib", "closing",
        lambda a: f"{_CL}.closing({a[0]})")

    register_lib_call("contextlib", "ExitStack",
        lambda a: f"{_CL}.ExitStack()")

    register_lib_call("contextlib", "asynccontextmanager",
        lambda a: f"{_CL}.asynccontextmanager({a[0]})")

    register_lib_call("contextlib", "AbstractContextManager",
        lambda a: f"{_CL}.AbstractContextManager")

    register_lib_call("contextlib", "chdir",
        lambda a: f"{_CL}.chdir({a[0]})")
