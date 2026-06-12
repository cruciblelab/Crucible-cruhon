"""
Compression & checksums for Cruhon — @zlib.*

Wraps Python's `zlib` module: DEFLATE compression and CRC32 / Adler-32
checksums. String inputs are auto-encoded to UTF-8 before compression.
No `@import` needed.

━━━ COMPRESS / DECOMPRESS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @zlib.compress[data]            → compressed bytes
  @zlib.compress[data; level]     → compress with level 0–9 (default -1)
  @zlib.decompress[data]          → original bytes
  @zlib.decompress_text[data]     → decompress then decode UTF-8 → str

━━━ CHECKSUMS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @zlib.crc32[data]               → CRC32 as unsigned int
  @zlib.crc32_hex[data]           → CRC32 as 8-char hex string
  @zlib.adler32[data]             → Adler-32 as unsigned int

━━━ STREAMING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @zlib.compressor[]              → zlib.compressobj() for streaming
  @zlib.decompressor[]            → zlib.decompressobj() for streaming

━━━ INFO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @zlib.ratio[original; compressed] → compression ratio (0.0–1.0)
"""
from ..registry import register_lib, register_lib_call

_Z = "__import__('zlib')"


def _as_bytes(expr: str) -> str:
    return f"({expr}.encode('utf-8') if isinstance({expr}, str) else {expr})"


def register():
    register_lib("zlib", "zlib")

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

    register_lib_call("zlib", "crc32",
        lambda a: f"({_Z}.crc32({_as_bytes(a[0])}) & 0xFFFFFFFF)")

    register_lib_call("zlib", "crc32_hex",
        lambda a: f"format({_Z}.crc32({_as_bytes(a[0])}) & 0xFFFFFFFF, '08x')")

    register_lib_call("zlib", "adler32",
        lambda a: f"({_Z}.adler32({_as_bytes(a[0])}) & 0xFFFFFFFF)")

    register_lib_call("zlib", "compressor",
        lambda a: f"{_Z}.compressobj({a[0]})" if a else f"{_Z}.compressobj()")

    register_lib_call("zlib", "decompressor",
        lambda a: f"{_Z}.decompressobj()")

    register_lib_call("zlib", "ratio",
        lambda a: (
            f"(len({a[1]}) / len({a[0]}) if len({a[0]}) else 0.0)"
            if len(a) > 1 else
            f"0.0"
        ))
