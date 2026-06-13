"""
cruhon/core/libs/pickle_.py
===========================
Pickle wrappers for Cruhon — @pickle.*

━━━ CORE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @pickle.dumps[obj]              → bytes
  @pickle.loads[data]             → object
  @pickle.dumps_proto[obj; n]     → bytes  (explicit protocol 0–5)
  @pickle.copy[obj]               → deep copy via round-trip

━━━ FILE I/O ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @pickle.save[path; obj]         — write to file
  @pickle.load[path]              → object
  @pickle.save_gz[path; obj]      — write gzip-compressed
  @pickle.load_gz[path]           → object

━━━ ENCODING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @pickle.to_base64[obj]          → str  (serialize → base64 string)
  @pickle.from_base64[text]       → object
  @pickle.to_hex[obj]             → str  (serialize → hex string)
  @pickle.from_hex[text]          → object

━━━ INSPECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @pickle.is_pickle[data]         → bool (check magic bytes)
  @pickle.size[obj]               → int  (serialized byte size)
  @pickle.protocol[data]          → int  (detect protocol version)
"""
from ..registry import register_lib, register_lib_call


def register():
    register_lib("pickle", None)

    # ── Core ──────────────────────────────────────────────────
    register_lib_call("pickle", "dumps",
        lambda a: f"__import__('pickle').dumps({a[0]})")

    register_lib_call("pickle", "loads",
        lambda a: f"__import__('pickle').loads({a[0]})")

    register_lib_call("pickle", "dumps_proto",
        lambda a: f"__import__('pickle').dumps({a[0]}, protocol=int({a[1]}))")

    register_lib_call("pickle", "copy",
        lambda a: f"__import__('pickle').loads(__import__('pickle').dumps({a[0]}))")

    # ── File I/O ──────────────────────────────────────────────
    register_lib_call("pickle", "save",
        lambda a: (
            f"(lambda _p, _o: open(_p, 'wb').write(__import__('pickle').dumps(_o)))({a[0]}, {a[1]})"
        ))

    register_lib_call("pickle", "load",
        lambda a: f"__import__('pickle').loads(open({a[0]}, 'rb').read())")

    register_lib_call("pickle", "save_gz",
        lambda a: (
            f"(lambda _p, _o: __import__('gzip').open(_p, 'wb').write(__import__('pickle').dumps(_o)))({a[0]}, {a[1]})"
        ))

    register_lib_call("pickle", "load_gz",
        lambda a: (
            f"__import__('pickle').loads(__import__('gzip').open({a[0]}, 'rb').read())"
        ))

    # ── Encoding ──────────────────────────────────────────────
    register_lib_call("pickle", "to_base64",
        lambda a: (
            f"__import__('base64').b64encode(__import__('pickle').dumps({a[0]})).decode('ascii')"
        ))

    register_lib_call("pickle", "from_base64",
        lambda a: (
            f"__import__('pickle').loads(__import__('base64').b64decode({a[0]}))"
        ))

    register_lib_call("pickle", "to_hex",
        lambda a: f"__import__('pickle').dumps({a[0]}).hex()")

    register_lib_call("pickle", "from_hex",
        lambda a: f"__import__('pickle').loads(bytes.fromhex({a[0]}))")

    # ── Inspect ───────────────────────────────────────────────
    register_lib_call("pickle", "is_pickle",
        lambda a: (
            f"(lambda _d: isinstance(_d, (bytes, bytearray)) and len(_d) >= 2 and _d[0] == 0x80 and _d[1] in range(6))({a[0]})"
        ))

    register_lib_call("pickle", "size",
        lambda a: f"len(__import__('pickle').dumps({a[0]}))")

    register_lib_call("pickle", "protocol",
        lambda a: (
            f"(lambda _d: _d[1] if isinstance(_d, (bytes, bytearray)) and len(_d) >= 2 and _d[0] == 0x80 else 0)({a[0]})"
        ))
