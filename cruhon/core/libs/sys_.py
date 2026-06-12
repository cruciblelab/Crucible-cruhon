"""Sys stdlib wrappers for Cruhon — @sys.*"""
from ..registry import register_lib, register_lib_call

_S = "__import__('sys')"


def register():
    register_lib("sys", "sys")

    register_lib_call("sys", "argv",
        lambda a: f"{_S}.argv")

    register_lib_call("sys", "argv_get",
        lambda a: f"{_S}.argv[{a[0]}]" if a else f"{_S}.argv[0]")

    register_lib_call("sys", "exit",
        lambda a: f"{_S}.exit({a[0] if a else 0})")

    register_lib_call("sys", "path",
        lambda a: f"{_S}.path")

    register_lib_call("sys", "path_append",
        lambda a: f"{_S}.path.append({a[0]})")

    register_lib_call("sys", "path_insert",
        lambda a: f"{_S}.path.insert({a[0]}, {a[1]})" if len(a) > 1 else f"{_S}.path.insert(0, {a[0]})")

    register_lib_call("sys", "version",
        lambda a: f"{_S}.version")

    register_lib_call("sys", "version_info",
        lambda a: f"{_S}.version_info")

    register_lib_call("sys", "platform",
        lambda a: f"{_S}.platform")

    register_lib_call("sys", "getsizeof",
        lambda a: f"{_S}.getsizeof({a[0]})")

    register_lib_call("sys", "getrecursionlimit",
        lambda a: f"{_S}.getrecursionlimit()")

    register_lib_call("sys", "setrecursionlimit",
        lambda a: f"{_S}.setrecursionlimit({a[0]})")

    register_lib_call("sys", "maxsize",
        lambda a: f"{_S}.maxsize")

    register_lib_call("sys", "stdin",
        lambda a: f"{_S}.stdin")

    register_lib_call("sys", "stdout",
        lambda a: f"{_S}.stdout")

    register_lib_call("sys", "stderr",
        lambda a: f"{_S}.stderr")

    register_lib_call("sys", "modules",
        lambda a: f"{_S}.modules")

    register_lib_call("sys", "executable",
        lambda a: f"{_S}.executable")

    register_lib_call("sys", "prefix",
        lambda a: f"{_S}.prefix")
