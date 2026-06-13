"""
cruhon/core/libs/plist_.py
==========================
Plistlib wrappers for Cruhon — @plist.*

Property list files (.plist) are a standard data format on macOS/iOS.
Python's plistlib reads and writes XML and binary plist formats.

  @plist.load[path]         → dict   (read plist file)
  @plist.save[path; data]   — write dict to plist file (XML format)
  @plist.loads[text]        → dict   (parse plist XML string)
  @plist.dumps[data]        → str    (dict → plist XML string)
  @plist.get[data; key]     → value
  @plist.get[data; key; default]
  @plist.to_json[data]      → JSON string
  @plist.from_json[text]    → dict   (JSON → plist-compatible dict)
"""
from ..registry import register_lib, register_lib_call


def register():
    register_lib("plist", None)

    register_lib_call("plist", "load",
        lambda a: f"(lambda _p: __import__('plistlib').loads(open(_p, 'rb').read()))({a[0]})")

    register_lib_call("plist", "save",
        lambda a: (
            f"(lambda _p, _d: open(_p, 'wb').write(__import__('plistlib').dumps(_d, fmt=__import__('plistlib').FMT_XML)))({a[0]}, {a[1]})"
        ))

    register_lib_call("plist", "loads",
        lambda a: (
            f"(lambda _s: __import__('plistlib').loads(_s if isinstance(_s, bytes) else _s.encode('utf-8')))({a[0]})"
        ))

    register_lib_call("plist", "dumps",
        lambda a: f"__import__('plistlib').dumps({a[0]}, fmt=__import__('plistlib').FMT_XML).decode('utf-8')")

    register_lib_call("plist", "get",
        lambda a: (
            f"{a[0]}.get({a[1]}, {a[2]})" if len(a) > 2 else
            f"{a[0]}.get({a[1]})"
        ))

    register_lib_call("plist", "to_json",
        lambda a: f"__import__('json').dumps({a[0]}, indent=2, default=str)")

    register_lib_call("plist", "from_json",
        lambda a: f"__import__('json').loads({a[0]})")
