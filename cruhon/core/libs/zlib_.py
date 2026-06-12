"""
Compression & checksums for Cruhon — @zlib.*

Wraps Python's `zlib` module: DEFLATE compression, CRC32 / Adler-32
checksums, streaming objects, and base64-wrapped helpers.
String inputs are auto-encoded to UTF-8 before compression.
No `@import` needed.

━━━ COMPRESS / DECOMPRESS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @zlib.compress[data]            → compressed bytes
  @zlib.compress[data; level]     → compress with level 0–9 (default -1)
  @zlib.decompress[data]          → original bytes
  @zlib.decompress_text[data]     → decompress then decode UTF-8 → str

━━━ BASE64 WRAPPERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @zlib.compress_b64[data]        → compress → base64-encoded bytes
  @zlib.decompress_b64[b64]       → base64-decode → decompress → bytes
  @zlib.compress_str[s]           → compress str → base64 ASCII string
  @zlib.decompress_str[s]         → base64 string → decompress → UTF-8 str

━━━ CHECKSUMS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @zlib.crc32[data]               → CRC32 as unsigned int
  @zlib.crc32_hex[data]           → CRC32 as 8-char hex string
  @zlib.adler32[data]             → Adler-32 as unsigned int
  @zlib.adler32_hex[data]         → Adler-32 as 8-char hex string

━━━ STREAMING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @zlib.compressor[]              → zlib.compressobj() for streaming
  @zlib.decompressor[]            → zlib.decompressobj() for streaming

━━━ INFO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @zlib.ratio[original; compressed] → compression ratio (0.0–1.0)
  @zlib.saved_bytes[data]           → bytes saved vs uncompressed size
  @zlib.is_zlib[data]               → True if bytes look like zlib-compressed data
"""
from ..registry import register_lib, register_lib_call

_Z = "__import__('zlib')"


def _as_bytes(expr: str) -> str:
    return f"({expr}.encode('utf-8') if isinstance({expr}, str) else {expr})"


def register():
    register_lib("zlib", "zlib")

    # ── COMPRESS / DECOMPRESS ────────────────────────────────
    register_lib_call("zlib", "compress",
        lambda a: (
            f"{_Z}.compress({_as_bytes(a[0])}, {a[1]})"
            if len(a) > 1 else
            f"{_Z}.compress({_as_bytes(a[0])})"
        ))

    register_lib_call("zlib", "decompress",
        lambda a: f"{_Z}.decompress({a[0]})")

    register_lib_call("zlib", "decompress_text",
        lambda a: f"{_Z}.decompress({a[0]}).decode('utf-8')")

    # ── BASE64 WRAPPERS ───────────────────────────────────────
    register_lib_call("zlib", "compress_b64",
        lambda a: (
            f"__import__('base64').b64encode({_Z}.compress({_as_bytes(a[0])}))"
            if a else "b''"
        ))

    register_lib_call("zlib", "decompress_b64",
        lambda a: (
            f"{_Z}.decompress(__import__('base64').b64decode({a[0]}))"
            if a else "b''"
        ))

    register_lib_call("zlib", "compress_str",
        lambda a: (
            f"__import__('base64').b64encode({_Z}.compress({_as_bytes(a[0])})).decode('ascii')"
            if a else "''"
        ))

    register_lib_call("zlib", "decompress_str",
        lambda a: (
            f"{_Z}.decompress(__import__('base64').b64decode({a[0]})).decode('utf-8')"
            if a else "''"
        ))

    # ── CHECKSUMS ─────────────────────────────────────────────
    register_lib_call("zlib", "crc32",
        lambda a: f"({_Z}.crc32({_as_bytes(a[0])}) & 0xFFFFFFFF)")

    register_lib_call("zlib", "crc32_hex",
        lambda a: f"format({_Z}.crc32({_as_bytes(a[0])}) & 0xFFFFFFFF, '08x')")

    register_lib_call("zlib", "adler32",
        lambda a: f"({_Z}.adler32({_as_bytes(a[0])}) & 0xFFFFFFFF)")

    register_lib_call("zlib", "adler32_hex",
        lambda a: (
            f"format({_Z}.adler32({_as_bytes(a[0])}) & 0xFFFFFFFF, '08x')"
            if a else "'00000000'"
        ))

    # ── STREAMING ─────────────────────────────────────────────
    register_lib_call("zlib", "compressor",
        lambda a: f"{_Z}.compressobj({a[0]})" if a else f"{_Z}.compressobj()")

    register_lib_call("zlib", "decompressor",
        lambda a: f"{_Z}.decompressobj()")

    # ── INFO ──────────────────────────────────────────────────
    register_lib_call("zlib", "ratio",
        lambda a: (
            f"(len({a[1]}) / len({a[0]}) if len({a[0]}) else 0.0)"
            if len(a) > 1 else
            f"0.0"
        ))

    register_lib_call("zlib", "saved_bytes",
        lambda a: (
            f"(lambda _d: len(_d) - len({_Z}.compress(_d)))({_as_bytes(a[0])})"
            if a else "0"
        ))

    register_lib_call("zlib", "is_zlib",
        lambda a: (
            f"(isinstance({a[0]}, (bytes, bytearray)) and len({a[0]}) >= 2 "
            f"and ({a[0]}[0] & 0x0f) == 8 "
            f"and ({a[0]}[0] * 256 + {a[0]}[1]) % 31 == 0)"
            if a else "False"
        ))
