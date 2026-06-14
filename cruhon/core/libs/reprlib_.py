"""
cruhon/core/libs/reprlib_.py
============================
Truncating object representations for Cruhon — @reprlib.*

Like repr() but limits the length of nested structures so you don't drown
in output when printing large collections.

━━━ REPR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @reprlib.repr[obj]              → truncated repr string (default limits)
  @reprlib.repr[obj; maxlen]      → cap repr at maxlen characters
  @reprlib.short[obj]             → very short repr (maxstring=20)

━━━ RECURSIVE REPR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @reprlib.recursive[fn]          → decorate fn to handle recursive reprs
"""
from ..registry import register_lib, register_lib_call

_RL = "__import__('reprlib')"


def register():
    register_lib("reprlib", None)

    register_lib_call("reprlib", "repr",
        lambda a: (
            f"(lambda _r, _o: (_r.__setattr__('maxstring', {a[1]}), _r.repr(_o))[1])"
            f"({_RL}.Repr(), {a[0]})"
            if len(a) > 1 else
            f"{_RL}.repr({a[0]})"
        ))
    register_lib_call("reprlib", "short",
        lambda a: (
            f"(lambda _r: (_r.__setattr__('maxstring', 20), _r.__setattr__('maxother', 20), "
            f"_r.repr({a[0]}))[2])({_RL}.Repr())"
        ))
    register_lib_call("reprlib", "recursive",
        lambda a: f"{_RL}.recursive_repr()({a[0]})")
