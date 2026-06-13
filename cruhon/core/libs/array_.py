"""
cruhon/core/libs/array_.py
==========================
Compact typed arrays for Cruhon — @array.*

Memory-efficient homogeneous numeric arrays (the stdlib `array` module).
Typecodes: 'b'/'B' int8, 'h'/'H' int16, 'i'/'I' int32, 'l'/'L' int32+,
'q'/'Q' int64, 'f' float32, 'd' float64, 'u' unicode.

━━━ CONSTRUCT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @array.of[typecode]             → empty typed array
  @array.of[typecode; iterable]   → array filled from iterable
  @array.zeros[typecode; n]       → array of n zeros
  @array.range[typecode; n]       → array of 0..n-1

━━━ BYTES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @array.to_bytes[arr]            → raw bytes representation
  @array.from_bytes[typecode; b]  → array reconstructed from bytes
  @array.to_list[arr]             → plain Python list
  @array.item_size[arr]           → bytes per element

━━━ INSPECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @array.typecode[arr]            → the array's typecode char
  @array.length[arr]              → number of elements
  @array.sum[arr]                 → sum of elements
  @array.min[arr] @array.max[arr] → extremes
"""
from ..registry import register_lib, register_lib_call

_AR = "__import__('array').array"


def register():
    register_lib("array", None)

    # ── Construct ─────────────────────────────────────────────
    register_lib_call("array", "of",
        lambda a: (
            f"{_AR}({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_AR}({a[0]})"
        ))

    register_lib_call("array", "zeros",
        lambda a: f"(lambda _t, _n: {_AR}(_t, [0] * _n))({a[0]}, {a[1]})")

    register_lib_call("array", "range",
        lambda a: f"(lambda _t, _n: {_AR}(_t, range(_n)))({a[0]}, {a[1]})")

    # ── Bytes ─────────────────────────────────────────────────
    register_lib_call("array", "to_bytes",
        lambda a: f"{a[0]}.tobytes()")

    register_lib_call("array", "from_bytes",
        lambda a: (
            f"(lambda _t, _b: (lambda _x: (_x.frombytes(_b), _x)[1])({_AR}(_t)))({a[0]}, {a[1]})"
        ))

    register_lib_call("array", "to_list",
        lambda a: f"{a[0]}.tolist()")

    register_lib_call("array", "item_size",
        lambda a: f"{a[0]}.itemsize")

    # ── Inspect ───────────────────────────────────────────────
    register_lib_call("array", "typecode",
        lambda a: f"{a[0]}.typecode")

    register_lib_call("array", "length",
        lambda a: f"len({a[0]})")

    register_lib_call("array", "sum",
        lambda a: f"sum({a[0]})")

    register_lib_call("array", "min",
        lambda a: f"min({a[0]})")

    register_lib_call("array", "max",
        lambda a: f"max({a[0]})")
