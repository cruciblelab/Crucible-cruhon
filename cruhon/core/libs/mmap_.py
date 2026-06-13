"""
cruhon/core/libs/mmap_.py
=========================
Memory-mapped file reads for Cruhon — @mmap.*

Read large files without loading them fully into memory. Each call opens
the file read-only, memory-maps it, performs the operation, and closes
cleanly.

━━━ READ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @mmap.read[path]                → entire file as bytes (via mmap)
  @mmap.slice[path; start; end]   → bytes[start:end]
  @mmap.size[path]                → mapped length in bytes

━━━ SEARCH ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @mmap.find[path; needle]        → byte offset of needle, or -1
  @mmap.contains[path; needle]    → bool
  @mmap.count[path; needle]       → number of occurrences
"""
from ..registry import register_lib, register_lib_call

# open path read-only, mmap it, run _body(_m), then close everything
_OPEN = (
    "(lambda _p, _body: (lambda _f: (lambda _m: (_body(_m), _m.close(), _f.close())[0])"
    "(__import__('mmap').mmap(_f.fileno(), 0, access=__import__('mmap').ACCESS_READ)))"
    "(open(_p, 'rb')))"
)


def register():
    register_lib("mmap", None)

    # ── Read ──────────────────────────────────────────────────
    register_lib_call("mmap", "read",
        lambda a: f"{_OPEN}({a[0]}, lambda _m: _m[:])")
    register_lib_call("mmap", "slice",
        lambda a: f"{_OPEN}({a[0]}, lambda _m: _m[{a[1]}:{a[2]}])")
    register_lib_call("mmap", "size",
        lambda a: f"{_OPEN}({a[0]}, lambda _m: len(_m))")

    # ── Search ────────────────────────────────────────────────
    register_lib_call("mmap", "find",
        lambda a: f"{_OPEN}({a[0]}, lambda _m: _m.find({a[1]}))")
    register_lib_call("mmap", "contains",
        lambda a: f"{_OPEN}({a[0]}, lambda _m: _m.find({a[1]}) != -1)")
    register_lib_call("mmap", "count",
        lambda a: f"{_OPEN}({a[0]}, lambda _m: _m[:].count({a[1]}))")
