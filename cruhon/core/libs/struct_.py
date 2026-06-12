"""
Binary packing for Cruhon — @struct.*

Wraps Python's `struct` module: convert between Python values and C
structs represented as bytes. Format strings follow the standard
struct syntax (e.g. ">I" big-endian unsigned int, "<2f" two little-endian
floats). No `@import` needed.

━━━ PACK / UNPACK ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @struct.pack[fmt; v1; v2; …]   → bytes
  @struct.unpack[fmt; data]      → tuple of values
  @struct.pack_into[fmt; buf; off; v…]  → pack into a writable buffer at offset
  @struct.unpack_from[fmt; data]        → unpack from start of buffer
  @struct.unpack_from[fmt; data; off]   → unpack from buffer at offset
  @struct.iter_unpack[fmt; data]        → iterator of tuples

━━━ INTROSPECTION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @struct.calcsize[fmt]          → byte size of the format
  @struct.compile[fmt]           → reusable struct.Struct object

A compiled Struct object exposes .pack / .unpack / .size in plain Python.
"""
from ..registry import register_lib, register_lib_call

_ST = "__import__('struct')"


def register():
    register_lib("struct", "struct")

    register_lib_call("struct", "pack",
        lambda a: (
            f"{_ST}.pack({a[0]}, {', '.join(a[1:])})"
            if len(a) > 1 else
            f"{_ST}.pack({a[0]})"
        ))

    register_lib_call("struct", "unpack",
        lambda a: f"{_ST}.unpack({a[0]}, {a[1]})" if len(a) > 1 else f"{_ST}.unpack({a[0]}, b'')")

    register_lib_call("struct", "pack_into",
        lambda a: (
            f"{_ST}.pack_into({a[0]}, {a[1]}, {a[2]}, {', '.join(a[3:])})"
            if len(a) > 3 else
            f"{_ST}.pack_into({a[0]}, {a[1]}, {a[2]})"
        ))

    register_lib_call("struct", "unpack_from",
        lambda a: (
            f"{_ST}.unpack_from({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"{_ST}.unpack_from({a[0]}, {a[1]})"
            if len(a) > 1 else
            f"{_ST}.unpack_from({a[0]})"
        ))

    register_lib_call("struct", "iter_unpack",
        lambda a: f"{_ST}.iter_unpack({a[0]}, {a[1]})" if len(a) > 1 else f"{_ST}.iter_unpack({a[0]}, b'')")

    register_lib_call("struct", "calcsize",
        lambda a: f"{_ST}.calcsize({a[0]})")

    register_lib_call("struct", "compile",
        lambda a: f"{_ST}.Struct({a[0]})")
