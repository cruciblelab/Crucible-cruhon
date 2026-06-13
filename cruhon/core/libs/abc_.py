"""
cruhon/core/libs/abc_.py
========================
Abstract base class helpers for Cruhon — @abc.*

Inspect and register abstract base classes without @raw.

━━━ INSPECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @abc.is_abstract[cls]           → bool: does cls have unimplemented methods
  @abc.abstract_methods[cls]      → set of abstract method names
  @abc.cache_token[]              → current ABC registry cache token

━━━ VIRTUAL SUBCLASSING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @abc.register[base; cls]        → register cls as a virtual subclass of base
  @abc.is_subclass[base; cls]     → issubclass(cls, base) (honours register)
  @abc.is_instance[base; obj]     → isinstance(obj, base) (honours register)
"""
from ..registry import register_lib, register_lib_call

_ABC = "__import__('abc')"


def register():
    register_lib("abc", None)

    # ── Inspect ───────────────────────────────────────────────
    register_lib_call("abc", "is_abstract",
        lambda a: f"bool(getattr({a[0]}, '__abstractmethods__', None))")
    register_lib_call("abc", "abstract_methods",
        lambda a: f"set(getattr({a[0]}, '__abstractmethods__', frozenset()))")
    register_lib_call("abc", "cache_token",
        lambda a: f"{_ABC}.get_cache_token()")

    # ── Virtual subclassing ───────────────────────────────────
    register_lib_call("abc", "register",
        lambda a: f"(lambda _b, _c: (_b.register(_c), _c)[1])({a[0]}, {a[1]})")
    register_lib_call("abc", "is_subclass",
        lambda a: f"issubclass({a[1]}, {a[0]})")
    register_lib_call("abc", "is_instance",
        lambda a: f"isinstance({a[1]}, {a[0]})")
