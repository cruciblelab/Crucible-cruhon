"""
cruhon/core/libs/codecs_.py
===========================
Character encoding and codec operations for Cruhon — @codecs.*

Encode and decode strings using Python's built-in codec system, including
special text transforms like ROT-13, hex, and zlib codecs.

━━━ ENCODE / DECODE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @codecs.encode[s; codec]        → codecs.encode(s, codec)
  @codecs.decode[b; codec]        → codecs.decode(b, codec)
  @codecs.encode_err[s; c; errs]  → encode with error handler
  @codecs.decode_err[b; c; errs]  → decode with error handler

━━━ TEXT TRANSFORMS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @codecs.rot13[s]                → ROT-13 transformation
  @codecs.hex[s]                  → hex-encode a string (bytes → hex string)
  @codecs.unhex[s]                → decode hex-encoded bytes
  @codecs.zip[data]               → zlib-compress bytes via codec
  @codecs.unzip[data]             → zlib-decompress bytes via codec

━━━ LOOKUP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @codecs.lookup[name]            → CodecInfo for the named codec
  @codecs.name[codec_info]        → codec name string
  @codecs.open[path; mode; enc]   → codecs.open(path, mode, enc)

━━━ ITERATORS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @codecs.reader[stream; enc]     → codecs.getreader(enc)(stream)
  @codecs.writer[stream; enc]     → codecs.getwriter(enc)(stream)
"""
from ..registry import register_lib, register_lib_call

_CD = "__import__('codecs')"


def register():
    register_lib("codecs", None)

    # ── Encode / Decode ───────────────────────────────────────
    register_lib_call("codecs", "encode",
        lambda a: f"{_CD}.encode({a[0]}, {a[1]})")
    register_lib_call("codecs", "decode",
        lambda a: f"{_CD}.decode({a[0]}, {a[1]})")
    register_lib_call("codecs", "encode_err",
        lambda a: f"{_CD}.encode({a[0]}, {a[1]}, {a[2]})")
    register_lib_call("codecs", "decode_err",
        lambda a: f"{_CD}.decode({a[0]}, {a[1]}, {a[2]})")

    # ── Text transforms ───────────────────────────────────────
    register_lib_call("codecs", "rot13",
        lambda a: f"{_CD}.encode({a[0]}, 'rot_13')")
    register_lib_call("codecs", "hex",
        lambda a: f"{_CD}.encode({a[0]}, 'hex_codec').decode('ascii')")
    register_lib_call("codecs", "unhex",
        lambda a: f"{_CD}.decode({a[0]}, 'hex_codec')")
    register_lib_call("codecs", "zip",
        lambda a: f"{_CD}.encode({a[0]}, 'zlib_codec')")
    register_lib_call("codecs", "unzip",
        lambda a: f"{_CD}.decode({a[0]}, 'zlib_codec')")

    # ── Lookup ────────────────────────────────────────────────
    register_lib_call("codecs", "lookup",
        lambda a: f"{_CD}.lookup({a[0]})")
    register_lib_call("codecs", "name",
        lambda a: f"{_CD}.lookup({a[0]}).name")
    register_lib_call("codecs", "open",
        lambda a: (
            f"{_CD}.open({a[0]}, {a[1]}, {a[2]})" if len(a) > 2 else
            f"{_CD}.open({a[0]}, {a[1]})"
        ))

    # ── Stream wrappers ───────────────────────────────────────
    register_lib_call("codecs", "reader",
        lambda a: f"{_CD}.getreader({a[1]})({a[0]})")
    register_lib_call("codecs", "writer",
        lambda a: f"{_CD}.getwriter({a[1]})({a[0]})")
