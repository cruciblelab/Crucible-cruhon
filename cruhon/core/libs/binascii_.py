"""
Binary ↔ ASCII conversions for Cruhon — @binascii.*

Wraps Python's `binascii` module: hex, base64, uuencode, and CRC helpers.
String inputs are auto-encoded to UTF-8 where bytes are required.
No `@import` needed.

━━━ HEX ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @binascii.hexlify[data]        → hex string (e.g. b"AB" → "4142")
  @binascii.hexlify[data; sep]   → hex string with a separator between bytes
  @binascii.unhexlify[hex]       → bytes from a hex string

━━━ BASE64 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @binascii.b2a_base64[data]     → base64-encoded bytes (with trailing newline)
  @binascii.a2b_base64[text]     → decode base64 back to bytes

━━━ CHECKSUM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @binascii.crc32[data]          → CRC32 as unsigned int
  @binascii.crc_hqx[data; value] → CRC-CCITT (HQX) checksum

━━━ MISC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @binascii.b2a_hex[data]        → alias of hexlify
  @binascii.a2b_hex[hex]         → alias of unhexlify
"""
from ..registry import register_lib, register_lib_call

_BA = "__import__('binascii')"


def _as_bytes(expr: str) -> str:
    return f"({expr}.encode('utf-8') if isinstance({expr}, str) else {expr})"


def register():
    register_lib("binascii", "binascii")

    # ── HEX ───────────────────────────────────────────────────
    register_lib_call("binascii", "hexlify",
        lambda a: (
            f"{_BA}.hexlify({_as_bytes(a[0])}, {a[1]}).decode('ascii')"
            if len(a) > 1 else
            f"{_BA}.hexlify({_as_bytes(a[0])}).decode('ascii')"
            if a else "''"
        ))

    register_lib_call("binascii", "unhexlify",
        lambda a: f"{_BA}.unhexlify({a[0]})" if a else "b''")

    register_lib_call("binascii", "b2a_hex",
        lambda a: f"{_BA}.b2a_hex({_as_bytes(a[0])}).decode('ascii')" if a else "''")

    register_lib_call("binascii", "a2b_hex",
        lambda a: f"{_BA}.a2b_hex({a[0]})" if a else "b''")

    # ── BASE64 ────────────────────────────────────────────────
    register_lib_call("binascii", "b2a_base64",
        lambda a: f"{_BA}.b2a_base64({_as_bytes(a[0])})" if a else "b''")

    register_lib_call("binascii", "a2b_base64",
        lambda a: f"{_BA}.a2b_base64({a[0]})" if a else "b''")

    # ── CHECKSUM ──────────────────────────────────────────────
    register_lib_call("binascii", "crc32",
        lambda a: f"({_BA}.crc32({_as_bytes(a[0])}) & 0xFFFFFFFF)" if a else "0")

    register_lib_call("binascii", "crc_hqx",
        lambda a: (
            f"{_BA}.crc_hqx({_as_bytes(a[0])}, {a[1]})"
            if len(a) > 1 else
            f"{_BA}.crc_hqx({_as_bytes(a[0])}, 0)"
            if a else "0"
        ))
