"""
cruhon/core/libs/plist_.py
==========================
Plistlib wrappers for Cruhon — @plist.*

Property list files (.plist) are the standard config/data format on
macOS and iOS. Python's plistlib supports XML and binary formats.

━━━ FILE I/O ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @plist.load[path]               → dict  (auto-detects XML or binary)
  @plist.save[path; data]         — write XML plist file
  @plist.load_binary[path]        → dict  (binary .plist file)
  @plist.save_binary[path; data]  — write binary plist file

━━━ STRING / BYTES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @plist.loads[text]              → dict  (parse XML plist string or bytes)
  @plist.dumps[data]              → str   (dict → XML plist string)
  @plist.loads_binary[data]       → dict  (parse binary plist bytes)
  @plist.dumps_binary[data]       → bytes (dict → binary plist bytes)

━━━ DICT HELPERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @plist.get[data; key]           → value or None
  @plist.get[data; key; default]
  @plist.set[data; key; value]    → new dict (non-destructive)
  @plist.has[data; key]           → bool
  @plist.keys[data]               → list of keys
  @plist.values[data]             → list of values
  @plist.items[data]              → list of (key, value) tuples
  @plist.merge[d1; d2]            → merged dict (d2 wins on conflict)
  @plist.remove[data; key]        → new dict without key

━━━ CONVERSION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @plist.to_json[data]            → JSON string
  @plist.from_json[text]          → dict
  @plist.to_dict[data]            → plain Python dict (recursively converts)
  @plist.fmt[path]                → "xml" or "binary"
"""
from ..registry import register_lib, register_lib_call

_PL = "__import__('plistlib')"
_FMT_XML = f"{_PL}.FMT_XML"
_FMT_BIN = f"{_PL}.FMT_BINARY"


def register():
    register_lib("plist", None)

    # ── File I/O ──────────────────────────────────────────────
    register_lib_call("plist", "load",
        lambda a: f"(lambda _p: {_PL}.loads(open(_p, 'rb').read()))({a[0]})")

    register_lib_call("plist", "save",
        lambda a: (
            f"(lambda _p, _d: open(_p, 'wb').write({_PL}.dumps(_d, fmt={_FMT_XML})))({a[0]}, {a[1]})"
        ))

    register_lib_call("plist", "load_binary",
        lambda a: (
            f"(lambda _p: {_PL}.loads(open(_p, 'rb').read(), fmt={_FMT_BIN}))({a[0]})"
        ))

    register_lib_call("plist", "save_binary",
        lambda a: (
            f"(lambda _p, _d: open(_p, 'wb').write({_PL}.dumps(_d, fmt={_FMT_BIN})))({a[0]}, {a[1]})"
        ))

    # ── String / Bytes ────────────────────────────────────────
    register_lib_call("plist", "loads",
        lambda a: (
            f"(lambda _s: {_PL}.loads(_s if isinstance(_s, bytes) else _s.encode('utf-8')))({a[0]})"
        ))

    register_lib_call("plist", "dumps",
        lambda a: f"{_PL}.dumps({a[0]}, fmt={_FMT_XML}).decode('utf-8')")

    register_lib_call("plist", "loads_binary",
        lambda a: (
            f"(lambda _d: {_PL}.loads(_d, fmt={_FMT_BIN}))({a[0]})"
        ))

    register_lib_call("plist", "dumps_binary",
        lambda a: f"{_PL}.dumps({a[0]}, fmt={_FMT_BIN})")

    # ── Dict helpers ──────────────────────────────────────────
    register_lib_call("plist", "get",
        lambda a: (
            f"{a[0]}.get({a[1]}, {a[2]})" if len(a) > 2 else
            f"{a[0]}.get({a[1]})"
        ))

    register_lib_call("plist", "set",
        lambda a: f"{{**{a[0]}, {a[1]}: {a[2]}}}")

    register_lib_call("plist", "has",
        lambda a: f"({a[1]} in {a[0]})")

    register_lib_call("plist", "keys",
        lambda a: f"list({a[0]}.keys())")

    register_lib_call("plist", "values",
        lambda a: f"list({a[0]}.values())")

    register_lib_call("plist", "items",
        lambda a: f"list({a[0]}.items())")

    register_lib_call("plist", "merge",
        lambda a: f"{{**{a[0]}, **{a[1]}}}")

    register_lib_call("plist", "remove",
        lambda a: f"{{_k: _v for _k, _v in {a[0]}.items() if _k != {a[1]}}}")

    # ── Conversion ────────────────────────────────────────────
    register_lib_call("plist", "to_json",
        lambda a: f"__import__('json').dumps({a[0]}, indent=2, default=str)")

    register_lib_call("plist", "from_json",
        lambda a: f"__import__('json').loads({a[0]})")

    register_lib_call("plist", "to_dict",
        lambda a: (
            f"(lambda _d: (lambda _f: _f(_f, _d))(lambda _self, _x: "
            f"{{_k: _self(_self, _v) for _k, _v in _x.items()}} if isinstance(_x, dict) else "
            f"[_self(_self, _i) for _i in _x] if isinstance(_x, list) else _x))({a[0]})"
        ))

    register_lib_call("plist", "fmt",
        lambda a: (
            f"(lambda _p: 'binary' if open(_p, 'rb').read(8).startswith(b'bplist') else 'xml')({a[0]})"
        ))
