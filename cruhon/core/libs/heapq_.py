"""Heapq stdlib wrappers for Cruhon — @heapq.*"""
from ..registry import register_lib, register_lib_call

_HQ = "__import__('heapq')"


def register():
    register_lib("heapq", "heapq")

    register_lib_call("heapq", "heappush",
        lambda a: f"{_HQ}.heappush({a[0]}, {a[1]})" if len(a) > 1 else f"{_HQ}.heappush({a[0]}, 0)")

    register_lib_call("heapq", "heappop",
        lambda a: f"{_HQ}.heappop({a[0]})")

    register_lib_call("heapq", "heapify",
        lambda a: f"{_HQ}.heapify({a[0]})")

    register_lib_call("heapq", "heappushpop",
        lambda a: f"{_HQ}.heappushpop({a[0]}, {a[1]})" if len(a) > 1 else f"{_HQ}.heappushpop({a[0]}, 0)")

    register_lib_call("heapq", "heapreplace",
        lambda a: f"{_HQ}.heapreplace({a[0]}, {a[1]})" if len(a) > 1 else f"{_HQ}.heapreplace({a[0]}, 0)")

    register_lib_call("heapq", "nlargest",
        lambda a: (
            f"{_HQ}.nlargest({a[0]}, {a[1]}, key={a[2]})" if len(a) > 2 else
            f"{_HQ}.nlargest({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_HQ}.nlargest(1, {a[0]})"
        ))

    register_lib_call("heapq", "nsmallest",
        lambda a: (
            f"{_HQ}.nsmallest({a[0]}, {a[1]}, key={a[2]})" if len(a) > 2 else
            f"{_HQ}.nsmallest({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_HQ}.nsmallest(1, {a[0]})"
        ))

    register_lib_call("heapq", "merge",
        lambda a: f"list({_HQ}.merge({', '.join(a)}))")
