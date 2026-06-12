"""Bisect stdlib wrappers for Cruhon — @bisect.*"""
from ..registry import register_lib, register_lib_call

_BI = "__import__('bisect')"


def register():
    register_lib("bisect", "bisect")

    register_lib_call("bisect", "bisect_left",
        lambda a: (
            f"{_BI}.bisect_left({a[0]}, {a[1]}, {a[2]}, {a[3]})" if len(a) > 3 else
            f"{_BI}.bisect_left({a[0]}, {a[1]}, {a[2]})" if len(a) > 2 else
            f"{_BI}.bisect_left({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_BI}.bisect_left({a[0]}, 0)"
        ))

    register_lib_call("bisect", "bisect_right",
        lambda a: (
            f"{_BI}.bisect_right({a[0]}, {a[1]}, {a[2]}, {a[3]})" if len(a) > 3 else
            f"{_BI}.bisect_right({a[0]}, {a[1]}, {a[2]})" if len(a) > 2 else
            f"{_BI}.bisect_right({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_BI}.bisect_right({a[0]}, 0)"
        ))

    register_lib_call("bisect", "bisect",
        lambda a: f"{_BI}.bisect({a[0]}, {a[1]})" if len(a) > 1 else f"{_BI}.bisect({a[0]}, 0)")

    register_lib_call("bisect", "insort_left",
        lambda a: f"{_BI}.insort_left({a[0]}, {a[1]})" if len(a) > 1 else f"{_BI}.insort_left({a[0]}, 0)")

    register_lib_call("bisect", "insort_right",
        lambda a: f"{_BI}.insort_right({a[0]}, {a[1]})" if len(a) > 1 else f"{_BI}.insort_right({a[0]}, 0)")

    register_lib_call("bisect", "insort",
        lambda a: f"{_BI}.insort({a[0]}, {a[1]})" if len(a) > 1 else f"{_BI}.insort({a[0]}, 0)")
