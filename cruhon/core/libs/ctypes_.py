"""
cruhon/core/libs/ctypes_.py
===========================
Foreign function interface for Cruhon — @ctypes.*

Call C library functions, create C-compatible data types, and manipulate
raw memory through Python's ctypes module.

━━━ LOAD LIBRARIES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ctypes.load[name]              → ctypes.CDLL(name)
  @ctypes.load_win[name]          → ctypes.WinDLL(name)
  @ctypes.load_util[name]         → load by short name (via ctypes.util)
  @ctypes.libc[]                  → ctypes.CDLL(None)  — libc on Unix

━━━ C TYPES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ctypes.c_int[v]                → ctypes.c_int(v)
  @ctypes.c_uint[v]               → ctypes.c_uint(v)
  @ctypes.c_long[v]               → ctypes.c_long(v)
  @ctypes.c_ulong[v]              → ctypes.c_ulong(v)
  @ctypes.c_float[v]              → ctypes.c_float(v)
  @ctypes.c_double[v]             → ctypes.c_double(v)
  @ctypes.c_bool[v]               → ctypes.c_bool(v)
  @ctypes.c_char[v]               → ctypes.c_char(v)
  @ctypes.c_char_p[s]             → ctypes.c_char_p(s)
  @ctypes.c_void_p[v]             → ctypes.c_void_p(v)
  @ctypes.c_size_t[v]             → ctypes.c_size_t(v)
  @ctypes.c_wchar_p[s]            → ctypes.c_wchar_p(s)

━━━ MEMORY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ctypes.create_buf[n]           → ctypes.create_string_buffer(n)
  @ctypes.create_wbuf[n]          → ctypes.create_unicode_buffer(n)
  @ctypes.string_at[addr]         → ctypes.string_at(addr)
  @ctypes.string_at[addr; size]   → ctypes.string_at(addr, size)
  @ctypes.wstring_at[addr]        → ctypes.wstring_at(addr)
  @ctypes.memmove[dst; src; n]    → ctypes.memmove(dst, src, n)
  @ctypes.memset[dst; c; n]       → ctypes.memset(dst, c, n)

━━━ POINTER UTILITIES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ctypes.byref[obj]              → ctypes.byref(obj)
  @ctypes.pointer[obj]            → ctypes.pointer(obj)
  @ctypes.addressof[obj]          → ctypes.addressof(obj)
  @ctypes.sizeof[type_or_obj]     → ctypes.sizeof(type_or_obj)
  @ctypes.cast[obj; type]         → ctypes.cast(obj, type)
  @ctypes.pointer_type[type]      → ctypes.POINTER(type)

━━━ VALUE ACCESS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ctypes.val[obj]                → obj.value
  @ctypes.set_val[obj; v]         → set obj.value = v (returns obj)
"""
from ..registry import register_lib, register_lib_call

_CT = "__import__('ctypes')"


def register():
    register_lib("ctypes", None)

    # ── Load libraries ────────────────────────────────────────
    register_lib_call("ctypes", "load",
        lambda a: f"{_CT}.CDLL({a[0]})")
    register_lib_call("ctypes", "load_win",
        lambda a: f"{_CT}.WinDLL({a[0]})")
    register_lib_call("ctypes", "load_util",
        lambda a: (
            f"(lambda _n: {_CT}.CDLL({_CT}.util.find_library(_n)))({a[0]})"
        ))
    register_lib_call("ctypes", "libc",
        lambda a: f"{_CT}.CDLL(None)")

    # ── C types ───────────────────────────────────────────────
    register_lib_call("ctypes", "c_int",
        lambda a: f"{_CT}.c_int({a[0]})" if a else f"{_CT}.c_int")
    register_lib_call("ctypes", "c_uint",
        lambda a: f"{_CT}.c_uint({a[0]})" if a else f"{_CT}.c_uint")
    register_lib_call("ctypes", "c_long",
        lambda a: f"{_CT}.c_long({a[0]})" if a else f"{_CT}.c_long")
    register_lib_call("ctypes", "c_ulong",
        lambda a: f"{_CT}.c_ulong({a[0]})" if a else f"{_CT}.c_ulong")
    register_lib_call("ctypes", "c_float",
        lambda a: f"{_CT}.c_float({a[0]})" if a else f"{_CT}.c_float")
    register_lib_call("ctypes", "c_double",
        lambda a: f"{_CT}.c_double({a[0]})" if a else f"{_CT}.c_double")
    register_lib_call("ctypes", "c_bool",
        lambda a: f"{_CT}.c_bool({a[0]})" if a else f"{_CT}.c_bool")
    register_lib_call("ctypes", "c_char",
        lambda a: f"{_CT}.c_char({a[0]})" if a else f"{_CT}.c_char")
    register_lib_call("ctypes", "c_char_p",
        lambda a: f"{_CT}.c_char_p({a[0]})" if a else f"{_CT}.c_char_p")
    register_lib_call("ctypes", "c_void_p",
        lambda a: f"{_CT}.c_void_p({a[0]})" if a else f"{_CT}.c_void_p")
    register_lib_call("ctypes", "c_size_t",
        lambda a: f"{_CT}.c_size_t({a[0]})" if a else f"{_CT}.c_size_t")
    register_lib_call("ctypes", "c_wchar_p",
        lambda a: f"{_CT}.c_wchar_p({a[0]})" if a else f"{_CT}.c_wchar_p")

    # ── Memory ────────────────────────────────────────────────
    register_lib_call("ctypes", "create_buf",
        lambda a: f"{_CT}.create_string_buffer({a[0]})")
    register_lib_call("ctypes", "create_wbuf",
        lambda a: f"{_CT}.create_unicode_buffer({a[0]})")
    register_lib_call("ctypes", "string_at",
        lambda a: (
            f"{_CT}.string_at({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_CT}.string_at({a[0]})"
        ))
    register_lib_call("ctypes", "wstring_at",
        lambda a: (
            f"{_CT}.wstring_at({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_CT}.wstring_at({a[0]})"
        ))
    register_lib_call("ctypes", "memmove",
        lambda a: f"{_CT}.memmove({a[0]}, {a[1]}, {a[2]})")
    register_lib_call("ctypes", "memset",
        lambda a: f"{_CT}.memset({a[0]}, {a[1]}, {a[2]})")

    # ── Pointer utilities ─────────────────────────────────────
    register_lib_call("ctypes", "byref",
        lambda a: f"{_CT}.byref({a[0]})")
    register_lib_call("ctypes", "pointer",
        lambda a: f"{_CT}.pointer({a[0]})")
    register_lib_call("ctypes", "addressof",
        lambda a: f"{_CT}.addressof({a[0]})")
    register_lib_call("ctypes", "sizeof",
        lambda a: f"{_CT}.sizeof({a[0]})")
    register_lib_call("ctypes", "cast",
        lambda a: f"{_CT}.cast({a[0]}, {a[1]})")
    register_lib_call("ctypes", "pointer_type",
        lambda a: f"{_CT}.POINTER({a[0]})")

    # ── Value access ──────────────────────────────────────────
    register_lib_call("ctypes", "val",
        lambda a: f"{a[0]}.value")
    register_lib_call("ctypes", "set_val",
        lambda a: f"(lambda _o, _v: (setattr(_o, 'value', _v), _o)[1])({a[0]}, {a[1]})")
