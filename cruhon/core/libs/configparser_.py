"""
cruhon/core/libs/configparser_.py
=================================
INI / config-file handling for Cruhon — @configparser.*

Read and write .ini / .cfg files with sections and key-value pairs.

━━━ LOAD ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @configparser.load[path]        → ConfigParser loaded from a file
  @configparser.loads[text]       → ConfigParser loaded from a string
  @configparser.new[]             → empty ConfigParser

━━━ READ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @configparser.get[cfg; section; key]    → value as string
  @configparser.getint[cfg; section; key] → value as int
  @configparser.getfloat[cfg; s; key]     → value as float
  @configparser.getbool[cfg; s; key]      → value as bool
  @configparser.sections[cfg]     → list of section names
  @configparser.keys[cfg; section]→ list of key names in a section
  @configparser.items[cfg; section]→ list of (key, value) pairs
  @configparser.has[cfg; section; key] → bool

━━━ WRITE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @configparser.set[cfg; section; key; value] → set a key
  @configparser.add_section[cfg; section]     → add a section
  @configparser.remove_section[cfg; section]  → delete a whole section
  @configparser.remove_key[cfg; section; key] → delete a single key
  @configparser.read_dict[cfg; data]          → load from a nested dict
  @configparser.to_dict[cfg]                  → whole config as nested dict
  @configparser.has_section[cfg; section]     → bool
  @configparser.save[cfg; path]               → write to a file
  @configparser.dumps[cfg]                    → serialise to a string
"""
from ..registry import register_lib, register_lib_call

_CP = "__import__('configparser')"
_IO = "__import__('io')"


def register():
    register_lib("configparser", None)

    # ── Load ──────────────────────────────────────────────────
    register_lib_call("configparser", "load",
        lambda a: (
            f"(lambda _p: (lambda _c: (_c.read(_p), _c)[1])"
            f"({_CP}.ConfigParser()))({a[0]})"
        ))
    register_lib_call("configparser", "loads",
        lambda a: (
            f"(lambda _t: (lambda _c: (_c.read_string(_t), _c)[1])"
            f"({_CP}.ConfigParser()))({a[0]})"
        ))
    register_lib_call("configparser", "new",
        lambda a: f"{_CP}.ConfigParser()")

    # ── Read ──────────────────────────────────────────────────
    register_lib_call("configparser", "get",
        lambda a: f"{a[0]}.get({a[1]}, {a[2]})")
    register_lib_call("configparser", "getint",
        lambda a: f"{a[0]}.getint({a[1]}, {a[2]})")
    register_lib_call("configparser", "getfloat",
        lambda a: f"{a[0]}.getfloat({a[1]}, {a[2]})")
    register_lib_call("configparser", "getbool",
        lambda a: f"{a[0]}.getboolean({a[1]}, {a[2]})")
    register_lib_call("configparser", "sections",
        lambda a: f"{a[0]}.sections()")
    register_lib_call("configparser", "keys",
        lambda a: f"list({a[0]}.options({a[1]}))")
    register_lib_call("configparser", "items",
        lambda a: f"list({a[0]}.items({a[1]}))")
    register_lib_call("configparser", "has",
        lambda a: f"{a[0]}.has_option({a[1]}, {a[2]})")

    # ── Write ─────────────────────────────────────────────────
    register_lib_call("configparser", "set",
        lambda a: f"{a[0]}.set({a[1]}, {a[2]}, str({a[3]}))")
    register_lib_call("configparser", "add_section",
        lambda a: f"{a[0]}.add_section({a[1]})")
    register_lib_call("configparser", "remove_section",
        lambda a: f"{a[0]}.remove_section({a[1]})")
    register_lib_call("configparser", "remove_key",
        lambda a: f"{a[0]}.remove_option({a[1]}, {a[2]})")
    register_lib_call("configparser", "read_dict",
        lambda a: f"(lambda _c, _d: (_c.read_dict(_d), _c)[1])({a[0]}, {a[1]})")
    register_lib_call("configparser", "to_dict",
        lambda a: f"(lambda _c: {{_s: dict(_c.items(_s)) for _s in _c.sections()}})({a[0]})")
    register_lib_call("configparser", "has_section",
        lambda a: f"{a[0]}.has_section({a[1]})")
    register_lib_call("configparser", "save",
        lambda a: (
            f"(lambda _c, _p: (lambda _f: (_c.write(_f), _f.close()))(open(_p, 'w')))({a[0]}, {a[1]})"
        ))
    register_lib_call("configparser", "dumps",
        lambda a: (
            f"(lambda _c: (lambda _s: (_c.write(_s), _s.getvalue())[1])({_IO}.StringIO()))({a[0]})"
        ))
