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
  @array.index[arr; x]            → first position of x
  @array.count_of[arr; x]         → how many times x occurs
  @array.get[arr; i]              → element at index i
  @array.slice[arr; i; j]         → sub-array arr[i:j]

━━━ MUTATE (returns the same array) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @array.append[arr; x]           → append x
  @array.extend[arr; seq]         → append every item of seq
  @array.insert[arr; i; x]        → insert x at index i
  @array.pop[arr]                 → remove & return last element
  @array.pop[arr; i]              → remove & return element i
  @array.remove[arr; x]          → remove first occurrence of x
  @array.set[arr; i; x]           → assign arr[i] = x
  @array.reverse[arr]             → reverse in place
  @array.concat[a; b]             → new array a + b
  @array.byteswap[arr]            → swap byte order in place

━━━ FILES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @array.to_file[arr; path]       → write raw bytes to a file
  @array.from_file[typecode; path; n] → read n items from a file
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

    register_lib_call("array", "index",
        lambda a: f"{a[0]}.index({a[1]})")

    register_lib_call("array", "count_of",
        lambda a: f"{a[0]}.count({a[1]})")

    register_lib_call("array", "get",
        lambda a: f"{a[0]}[{a[1]}]")

    register_lib_call("array", "slice",
        lambda a: f"{a[0]}[{a[1]}:{a[2]}]")

    # ── Mutate (return the array for chaining) ────────────────
    register_lib_call("array", "append",
        lambda a: f"(lambda _a, _x: (_a.append(_x), _a)[1])({a[0]}, {a[1]})")

    register_lib_call("array", "extend",
        lambda a: f"(lambda _a, _s: (_a.extend(_s), _a)[1])({a[0]}, {a[1]})")

    register_lib_call("array", "insert",
        lambda a: f"(lambda _a, _i, _x: (_a.insert(_i, _x), _a)[1])({a[0]}, {a[1]}, {a[2]})")

    register_lib_call("array", "pop",
        lambda a: f"{a[0]}.pop({a[1]})" if len(a) > 1 else f"{a[0]}.pop()")

    register_lib_call("array", "remove",
        lambda a: f"(lambda _a, _x: (_a.remove(_x), _a)[1])({a[0]}, {a[1]})")

    register_lib_call("array", "set",
        lambda a: f"(lambda _a, _i, _x: (_a.__setitem__(_i, _x), _a)[1])({a[0]}, {a[1]}, {a[2]})")

    register_lib_call("array", "reverse",
        lambda a: f"(lambda _a: (_a.reverse(), _a)[1])({a[0]})")

    register_lib_call("array", "concat",
        lambda a: f"({a[0]} + {a[1]})")

    register_lib_call("array", "byteswap",
        lambda a: f"(lambda _a: (_a.byteswap(), _a)[1])({a[0]})")

    # ── Files ─────────────────────────────────────────────────
    register_lib_call("array", "to_file",
        lambda a: (
            f"(lambda _a, _p: (lambda _f: (_a.tofile(_f), _f.close())[1])(open(_p, 'wb')))({a[0]}, {a[1]})"
        ))

    register_lib_call("array", "from_file",
        lambda a: (
            f"(lambda _t, _p, _n: (lambda _a: (lambda _f: (_a.fromfile(_f, _n), _f.close(), _a)[2])"
            f"(open(_p, 'rb')))({_AR}(_t)))({a[0]}, {a[1]}, {a[2]})"
        ))

